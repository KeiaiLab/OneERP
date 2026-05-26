"""CODEF 4대보험 API 클라이언트 — Protocol + Mock + Real 구현.

CODEF API를 통해 4대보험 가입 현황, 납부 내역, 가입자 목록을 조회한다.
ONEERP_CODEF_API_URL 미설정 시 MockCODEFClient를 사용한다.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

import httpx

from oneerp_accounting_app.config import AccountingSettings, get_accounting_settings

logger = logging.getLogger(__name__)


class CODEFClient(Protocol):
    """CODEF 4대보험 API 인터페이스."""

    async def get_insurance_status(self, business_no: str) -> dict[str, Any]:
        """사업장의 4대보험 가입 현황을 조회한다."""
        ...

    async def get_payment_history(
        self,
        business_no: str,
        *,
        year: str,
        month: str,
    ) -> list[dict[str, Any]]:
        """4대보험 납부 내역을 조회한다."""
        ...

    async def get_subscribers(self, business_no: str) -> list[dict[str, Any]]:
        """4대보험 가입자 목록을 조회한다."""
        ...


class MockCODEFClient:
    """CODEF API Mock — 개발/테스트 환경에서 사용."""

    async def get_insurance_status(self, business_no: str) -> dict[str, Any]:
        """4대보험 가입 현황 Mock — 전체 가입 상태를 반환한다."""
        logger.info("Mock CODEF 가입 현황 조회: business_no=%s", business_no)
        return {
            "business_no": business_no,
            "national_pension": "가입",
            "health_insurance": "가입",
            "employment_insurance": "가입",
            "industrial_accident": "가입",
        }

    async def get_payment_history(
        self,
        business_no: str,  # noqa: ARG002
        *,
        year: str,
        month: str,
    ) -> list[dict[str, Any]]:
        """납부 내역 Mock — 빈 목록을 반환한다."""
        logger.info("Mock CODEF 납부 내역 조회: %s-%s", year, month)
        return []

    async def get_subscribers(
        self,
        business_no: str,  # noqa: ARG002
    ) -> list[dict[str, Any]]:
        """가입자 목록 Mock — 빈 목록을 반환한다."""
        logger.info("Mock CODEF 가입자 목록 조회")
        return []


class RealCODEFClient:
    """CODEF REST API 클라이언트 — httpx.AsyncClient 기반."""

    def __init__(self, api_url: str, api_key: str, api_secret: str) -> None:
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key
        self._api_secret = api_secret
        self._access_token: str | None = None

    async def _ensure_token(self) -> str:
        """CODEF OAuth 토큰을 갱신하거나 캐시된 토큰을 반환한다."""
        if self._access_token:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_url}/oauth/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": self._api_key,
                    "client_secret": self._api_secret,
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

    async def get_insurance_status(self, business_no: str) -> dict[str, Any]:
        """CODEF API로 4대보험 가입 현황을 조회한다."""
        headers = await self._auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_url}/v1/kr/insurance/status",
                json={"business_no": business_no},
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    async def get_payment_history(
        self,
        business_no: str,
        *,
        year: str,
        month: str,
    ) -> list[dict[str, Any]]:
        """CODEF API로 4대보험 납부 내역을 조회한다."""
        headers = await self._auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_url}/v1/kr/insurance/payment-history",
                json={
                    "business_no": business_no,
                    "year": year,
                    "month": month,
                },
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get("data", [])

    async def get_subscribers(self, business_no: str) -> list[dict[str, Any]]:
        """CODEF API로 4대보험 가입자 목록을 조회한다."""
        headers = await self._auth_headers()
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_url}/v1/kr/insurance/subscribers",
                json={"business_no": business_no},
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get("data", [])


def create_codef_client(
    settings: AccountingSettings | None = None,
) -> CODEFClient:
    """설정 기반 CODEF 클라이언트 팩토리.

    ONEERP_CODEF_API_URL 미설정 시 MockCODEFClient를 반환한다.
    """
    if settings is None:
        settings = get_accounting_settings()

    if settings.codef_api_url:
        logger.info("CODEF API 연동 모드: %s", settings.codef_api_url)
        return RealCODEFClient(
            api_url=settings.codef_api_url,
            api_key=settings.codef_api_key,
            api_secret=settings.codef_api_secret,
        )

    logger.info("ONEERP_CODEF_API_URL 미설정 — MockCODEFClient 사용")
    return MockCODEFClient()
