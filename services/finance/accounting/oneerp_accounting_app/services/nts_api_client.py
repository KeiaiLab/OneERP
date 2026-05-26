"""국세청 API 클라이언트 — Protocol + Mock 구현.

Phase 2에서는 MockNTSApiClient를 사용하며,
실제 국세청 API 연동은 환경변수 기반으로 전환한다.
"""

from __future__ import annotations

import logging
import os
from typing import Protocol
from uuid import uuid4

logger = logging.getLogger(__name__)


class NTSApiClient(Protocol):
    """국세청 API 클라이언트 인터페이스."""

    async def submit_invoice(self, invoice_data: dict) -> dict:
        """전자세금계산서를 국세청에 전송한다."""
        ...

    async def check_status(self, confirmation_no: str) -> dict:
        """국세청 전송 상태를 조회한다."""
        ...

    async def cancel_invoice(self, confirmation_no: str, reason: str) -> dict:
        """국세청 전송을 취소한다."""
        ...


class MockNTSApiClient:
    """국세청 API Mock — Phase 2에서 사용.

    실제 국세청 API 연동 전까지 Mock 응답을 반환한다.
    """

    async def submit_invoice(self, invoice_data: dict) -> dict:  # noqa: ARG002
        """전자세금계산서 전송 Mock — 항상 성공 응답을 반환한다."""
        confirmation_no = f"NTS-{uuid4().hex[:8]}"
        logger.info("Mock 국세청 전송: confirmation_no=%s", confirmation_no)
        return {
            "status": "accepted",
            "confirmation_no": confirmation_no,
            "message": "전송 완료",
        }

    async def check_status(self, confirmation_no: str) -> dict:
        """전송 상태 조회 Mock — 항상 confirmed 응답을 반환한다."""
        logger.info("Mock 국세청 상태 조회: confirmation_no=%s", confirmation_no)
        return {
            "status": "confirmed",
            "confirmation_no": confirmation_no,
        }

    async def cancel_invoice(self, confirmation_no: str, reason: str) -> dict:
        """전송 취소 Mock — 항상 cancelled 응답을 반환한다."""
        logger.info(
            "Mock 국세청 취소: confirmation_no=%s, reason=%s",
            confirmation_no,
            reason,
        )
        return {
            "status": "cancelled",
            "confirmation_no": confirmation_no,
        }


def create_nts_client(*, use_barobill: bool | None = None) -> NTSApiClient:
    """환경변수 기반 클라이언트 팩토리.

    ONEERP_NTS_API_URL 미설정 시 MockNTSApiClient를 반환한다.

    Args:
        use_barobill: True이면 바로빌 클라이언트를 통해 국세청 전송을 위임한다.
            None이면 ONEERP_NTS_USE_BAROBILL 환경변수로 판단한다.
    """
    if use_barobill is None:
        use_barobill = os.environ.get("ONEERP_NTS_USE_BAROBILL", "").lower() in (
            "true",
            "1",
            "yes",
        )

    if use_barobill:
        logger.info("국세청 전송을 바로빌 클라이언트에 위임합니다")
        # 바로빌 위임 시에도 NTSApiClient 인터페이스로 반환
        # 실제 위임 로직은 ETaxService에서 BarobillClient를 직접 사용

    nts_api_url = os.environ.get("ONEERP_NTS_API_URL")
    if nts_api_url:
        # Phase 3+: 실제 국세청 API 클라이언트 반환
        logger.info("국세청 API URL 설정됨: %s — 현재 Mock 사용", nts_api_url)
    else:
        logger.info("ONEERP_NTS_API_URL 미설정 — MockNTSApiClient 사용")
    return MockNTSApiClient()
