"""accounting 서비스의 Create/Update/Request/Response DTO 집약 (OE004).

models/는 Document(영속 상태)만 정의하고, API 경계에서 받는 요청 DTO는 여기에 모은다.
"""

from __future__ import annotations

from datetime import date  # noqa: TC003
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from .models.journal_entry import JournalEntryItem, _validate_balanced_items


class JournalEntryCreate(BaseModel):
    """분개전표 생성 요청 스키마 — L2 API 계약 5.1."""

    posting_date: date
    voucher_type: str = "journal_entry"
    items: list[JournalEntryItem] = Field(default_factory=list)
    remark: str = ""

    @model_validator(mode="after")
    def _차대변_일치_및_최소라인_검증(self) -> JournalEntryCreate:
        """BR-ACCT-002: 최소 라인 수 ≥ 2, BR-ACCT-001: 차대변 일치."""
        _validate_balanced_items(self.items)
        return self


class JournalEntryUpdate(BaseModel):
    """분개전표 수정 요청 스키마 — L2 API 계약 5.2."""

    posting_date: date | None = None
    voucher_type: str | None = None
    items: list[JournalEntryItem] | None = None
    remark: str | None = None

    @model_validator(mode="after")
    def _차대변_일치_및_최소라인_검증(self) -> JournalEntryUpdate:
        """items가 제공된 경우 BR-ACCT-001/002 검증."""
        _validate_balanced_items(self.items)
        return self


class AccountsReceivableCreate(BaseModel):
    """매출채권 리포트 생성 요청 스키마."""

    customer: str
    outstanding_amount: Decimal = Decimal(0)
    due_date: date | None = None
    aging_bucket: str = ""
    invoice_id: str = ""


class AccountsReceivableUpdate(BaseModel):
    """매출채권 리포트 수정 요청 스키마."""

    customer: str | None = None
    outstanding_amount: Decimal | None = None
    due_date: date | None = None
    aging_bucket: str | None = None
    invoice_id: str | None = None
