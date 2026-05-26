"""이연비용 전표(DeferredExpenseEntry) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class DeferredExpenseEntryStatus(StrEnum):
    """이연비용 전표 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class DeferredExpenseEntryCreate(BaseModel):
    """이연비용 전표 생성 요청 스키마."""

    account_id: str
    original_amount: Decimal = Decimal(0)
    recognized_amount: Decimal = Decimal(0)
    remaining_amount: Decimal = Decimal(0)
    start_date: date | None = None
    end_date: date | None = None


class DeferredExpenseEntryUpdate(BaseModel):
    """이연비용 전표 수정 요청 스키마."""

    account_id: str | None = None
    original_amount: Decimal | None = None
    recognized_amount: Decimal | None = None
    remaining_amount: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None


class DeferredExpenseEntry(BaseDocument):
    """이연비용 전표 문서."""

    status: DeferredExpenseEntryStatus = Field(
        default=DeferredExpenseEntryStatus.DRAFT,
        description="이연비용 전표 상태",
    )
    account_id: str = ""
    original_amount: Decimal = Decimal(0)
    recognized_amount: Decimal = Decimal(0)
    remaining_amount: Decimal = Decimal(0)
    start_date: date | None = None
    end_date: date | None = None
