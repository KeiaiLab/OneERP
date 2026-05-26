"""기간마감전표(Period Closing Voucher) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class PeriodClosingVoucherCreate(BaseModel):
    """기간마감전표 생성 요청 스키마."""

    fiscal_year: str
    closing_account: str
    posting_date: date | None = None
    remarks: str = ""


class PeriodClosingVoucherUpdate(BaseModel):
    """기간마감전표 수정 요청 스키마."""

    fiscal_year: str | None = None
    closing_account: str | None = None
    posting_date: date | None = None
    remarks: str | None = None


class PeriodClosingVoucher(BaseDocument):
    """기간마감전표 문서 — 회계 기간 마감 처리.

    naming prefix: PCV
    """

    fiscal_year: str = ""
    closing_account: str = ""
    posting_date: date | None = None
    remarks: str = ""
