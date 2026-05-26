"""POS 영수증(POSReceipt) 로그 모델."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class POSReceiptCreate(BaseModel):
    """POS 영수증 생성 요청 스키마."""

    transaction_id: str = ""
    receipt_data: str = ""
    printed_at: datetime | None = None


class POSReceipt(BaseDocument):
    """POS 영수증 로그 — 출력 이력 기록용.

    naming prefix: POSR
    """

    transaction_id: str = ""
    receipt_data: str = ""
    printed_at: datetime | None = None
