"""바로빌 전자세금계산서 API 클라이언트 — Protocol + Mock + Real 구현.

바로빌 REST API를 통해 전자세금계산서를 발급/취소/조회한다.
ONEERP_BAROBILL_API_URL 미설정 시 MockBarobillClient를 사용한다.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol
from uuid import uuid4

import httpx

from oneerp_accounting_app.config import AccountingSettings, get_accounting_settings

logger = logging.getLogger(__name__)


class BarobillClient(Protocol):
    """바로빌 전자세금계산서 API 인터페이스."""

    async def issue_tax_invoice(self, invoice_data: dict[str, Any]) -> dict[str, Any]:
        """전자세금계산서를 발급한다."""
        ...

    async def cancel_tax_invoice(self, confirmation_no: str, reason: str) -> dict[str, Any]:
        """전자세금계산서를 취소한다."""
        ...

    async def get_status(self, confirmation_no: str) -> dict[str, Any]:
        """전자세금계산서 상태를 조회한다."""
        ...

    async def list_invoices(self, *, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """기간별 전자세금계산서 목록을 조회한다."""
        ...


class MockBarobillClient:
    """바로빌 API Mock — 개발/테스트 환경에서 사용."""

    async def issue_tax_invoice(self, invoice_data: dict[str, Any]) -> dict[str, Any]:  # noqa: ARG002
        """전자세금계산서 발급 Mock — UUID 기반 확인번호를 반환한다."""
        confirmation_no = f"BB-{uuid4().hex[:8]}"
        logger.info("Mock 바로빌 발급: confirmation_no=%s", confirmation_no)
        return {
            "status": "issued",
            "confirmation_no": confirmation_no,
            "message": "발급 완료",
        }

    async def cancel_tax_invoice(self, confirmation_no: str, reason: str) -> dict[str, Any]:
        """전자세금계산서 취소 Mock — 항상 성공 응답을 반환한다."""
        logger.info(
            "Mock 바로빌 취소: confirmation_no=%s, reason=%s",
            confirmation_no,
            reason,
        )
        return {
            "status": "cancelled",
            "confirmation_no": confirmation_no,
            "message": "취소 완료",
        }

    async def get_status(self, confirmation_no: str) -> dict[str, Any]:
        """전자세금계산서 상태 조회 Mock — 항상 issued 응답을 반환한다."""
        logger.info("Mock 바로빌 상태 조회: confirmation_no=%s", confirmation_no)
        return {
            "status": "issued",
            "confirmation_no": confirmation_no,
        }

    async def list_invoices(self, *, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """기간별 목록 조회 Mock — 빈 목록을 반환한다."""
        logger.info("Mock 바로빌 목록 조회: %s ~ %s", start_date, end_date)
        return []


class RealBarobillClient:
    """바로빌 REST API 클라이언트 — httpx.AsyncClient 기반."""

    def __init__(self, api_url: str, api_key: str) -> None:
        self._api_url = api_url.rstrip("/")
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        """공통 인증 헤더를 반환한다."""
        return {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

    async def issue_tax_invoice(self, invoice_data: dict[str, Any]) -> dict[str, Any]:
        """바로빌 API로 전자세금계산서를 발급한다."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_url}/tax-invoices",
                json=invoice_data,
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def cancel_tax_invoice(self, confirmation_no: str, reason: str) -> dict[str, Any]:
        """바로빌 API로 전자세금계산서를 취소한다."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self._api_url}/tax-invoices/{confirmation_no}/cancel",
                json={"reason": reason},
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def get_status(self, confirmation_no: str) -> dict[str, Any]:
        """바로빌 API로 전자세금계산서 상태를 조회한다."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_url}/tax-invoices/{confirmation_no}",
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()

    async def list_invoices(self, *, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """바로빌 API로 기간별 전자세금계산서 목록을 조회한다."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self._api_url}/tax-invoices",
                params={"start_date": start_date, "end_date": end_date},
                headers=self._headers(),
            )
            response.raise_for_status()
            return response.json()


def create_barobill_client(
    settings: AccountingSettings | None = None,
) -> BarobillClient:
    """설정 기반 바로빌 클라이언트 팩토리.

    ONEERP_BAROBILL_API_URL 미설정 시 MockBarobillClient를 반환한다.
    """
    if settings is None:
        settings = get_accounting_settings()

    if settings.barobill_api_url:
        logger.info("바로빌 API 연동 모드: %s", settings.barobill_api_url)
        return RealBarobillClient(
            api_url=settings.barobill_api_url,
            api_key=settings.barobill_api_key,
        )

    logger.info("ONEERP_BAROBILL_API_URL 미설정 — MockBarobillClient 사용")
    return MockBarobillClient()
