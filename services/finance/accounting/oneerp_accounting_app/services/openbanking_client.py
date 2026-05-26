"""금융결제원 오픈뱅킹 API 클라이언트 — Protocol + Mock + Real 구현.

은행 계좌 조회, 거래내역, 잔액 조회, 이체 기능을 제공한다.
ONEERP_OPENBANKING_API_URL 미설정 시 MockOpenBankingClient를 사용한다.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import uuid4

import httpx

from oneerp_accounting_app.config import AccountingSettings, get_accounting_settings

logger = logging.getLogger(__name__)


class OpenBankingClient(Protocol):
    """금융결제원 오픈뱅킹 API 인터페이스."""

    async def get_accounts(self, user_seq_no: str) -> list[dict[str, Any]]:
        """사용자 등록 계좌 목록을 조회한다."""
        ...

    async def get_transactions(
        self,
        fintech_use_num: str,
        *,
        from_date: str,
        to_date: str,
    ) -> list[dict[str, Any]]:
        """계좌 거래내역을 조회한다."""
        ...

    async def get_balance(self, fintech_use_num: str) -> dict[str, Any]:
        """계좌 잔액을 조회한다."""
        ...

    async def transfer(
        self,
        *,
        from_fintech_use_num: str,
        to_bank_code: str,
        to_account_num: str,
        amount: int,
        memo: str,
    ) -> dict[str, Any]:
        """계좌 이체를 실행한다."""
        ...


class MockOpenBankingClient:
    """오픈뱅킹 API Mock — 개발/테스트 환경에서 사용."""

    async def get_accounts(self, user_seq_no: str) -> list[dict[str, Any]]:  # noqa: ARG002
        """계좌 목록 조회 Mock — 샘플 계좌 1건을 반환한다."""
        logger.info("Mock 오픈뱅킹 계좌 목록 조회")
        return [
            {
                "fintech_use_num": f"MOCK-{uuid4().hex[:12]}",
                "bank_code": "004",
                "bank_name": "KB국민은행",
                "account_num_masked": "***-****-1234",
                "account_holder_name": "테스트사용자",
            },
        ]

    async def get_transactions(
        self,
        fintech_use_num: str,  # noqa: ARG002
        *,
        from_date: str,
        to_date: str,
    ) -> list[dict[str, Any]]:
        """거래내역 조회 Mock — 빈 목록을 반환한다."""
        logger.info("Mock 오픈뱅킹 거래내역 조회: %s ~ %s", from_date, to_date)
        return []

    async def get_balance(self, fintech_use_num: str) -> dict[str, Any]:  # noqa: ARG002
        """잔액 조회 Mock — 0원 잔액을 반환한다."""
        logger.info("Mock 오픈뱅킹 잔액 조회")
        return {
            "balance_amount": 0,
            "available_amount": 0,
            "currency": "KRW",
            "queried_at": datetime.now(tz=UTC).isoformat(),
        }

    async def transfer(
        self,
        *,
        from_fintech_use_num: str,  # noqa: ARG002
        to_bank_code: str,  # noqa: ARG002
        to_account_num: str,  # noqa: ARG002
        amount: int,
        memo: str,  # noqa: ARG002
    ) -> dict[str, Any]:
        """이체 Mock — 항상 성공 응답을 반환한다."""
        transfer_no = f"TRF-{uuid4().hex[:8]}"
        logger.info("Mock 오픈뱅킹 이체: transfer_no=%s, amount=%d", transfer_no, amount)
        return {
            "status": "completed",
            "transfer_no": transfer_no,
            "amount": amount,
            "message": "이체 완료",
        }


class RealOpenBankingClient:
    """금융결제원 오픈뱅킹 REST API 클라이언트 — OAuth2 토큰 관리 포함."""

    def __init__(
        self,
        api_url: str,
        client_id: str,
        client_secret: str,
    ) -> None:
        self._api_url = api_url.rstrip("/")
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token: str | None = None

    async def _ensure_token(self) -> str:
        """OAuth2 액세스 토큰을 갱신하거나 캐시된 토큰을 반환한다."""
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_url}/oauth/2.0/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "scope": "oob",
                },
            )
            response.raise_for_status()
            token_data = response.json()
            self._access_token = token_data["access_token"]
            return self._access_token

    async def _auth_headers(self) -> dict[str, str]:
        """인증 헤더를 반환한다."""
        token = await self._ensure_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    async def get_accounts(self, user_seq_no: str) -> list[dict[str, Any]]:
        """오픈뱅킹 API로 계좌 목록을 조회한다."""
        headers = await self._auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_url}/v2.0/account/list",
                params={"user_seq_no": user_seq_no},
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get("res_list", [])

    async def get_transactions(
        self,
        fintech_use_num: str,
        *,
        from_date: str,
        to_date: str,
    ) -> list[dict[str, Any]]:
        """오픈뱅킹 API로 거래내역을 조회한다."""
        headers = await self._auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_url}/v2.0/account/transaction-list",
                params={
                    "fintech_use_num": fintech_use_num,
                    "from_date": from_date,
                    "to_date": to_date,
                    "sort_order": "D",
                },
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get("res_list", [])

    async def get_balance(self, fintech_use_num: str) -> dict[str, Any]:
        """오픈뱅킹 API로 잔액을 조회한다."""
        headers = await self._auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_url}/v2.0/account/balance",
                params={"fintech_use_num": fintech_use_num},
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    async def transfer(
        self,
        *,
        from_fintech_use_num: str,
        to_bank_code: str,
        to_account_num: str,
        amount: int,
        memo: str,
    ) -> dict[str, Any]:
        """오픈뱅킹 API로 이체를 실행한다."""
        headers = await self._auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_url}/v2.0/transfer/withdraw/fin_num",
                json={
                    "wd_pass_phrase": "NONE",
                    "wd_print_content": memo,
                    "fintech_use_num": from_fintech_use_num,
                    "tran_amt": str(amount),
                    "recv_client_bank_code": to_bank_code,
                    "recv_client_account_num": to_account_num,
                },
                headers=headers,
            )
            response.raise_for_status()
            return response.json()


def create_openbanking_client(
    settings: AccountingSettings | None = None,
) -> OpenBankingClient:
    """설정 기반 오픈뱅킹 클라이언트 팩토리.

    ONEERP_OPENBANKING_API_URL 미설정 시 MockOpenBankingClient를 반환한다.
    """
    if settings is None:
        settings = get_accounting_settings()

    if settings.openbanking_api_url:
        logger.info("오픈뱅킹 API 연동 모드: %s", settings.openbanking_api_url)
        return RealOpenBankingClient(
            api_url=settings.openbanking_api_url,
            client_id=settings.openbanking_client_id,
            client_secret=settings.openbanking_client_secret,
        )

    logger.info("ONEERP_OPENBANKING_API_URL 미설정 — MockOpenBankingClient 사용")
    return MockOpenBankingClient()
