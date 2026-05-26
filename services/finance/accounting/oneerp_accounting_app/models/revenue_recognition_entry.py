"""수익인식 전표(RevenueRecognitionEntry) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class RevenueRecognitionEntryStatus(StrEnum):
    """수익인식 전표 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class RevenueRecognitionEntryCreate(BaseModel):
    """수익인식 전표 생성 요청 스키마."""

    rule_id: str
    amount: Decimal = Decimal(0)
    recognition_date: date | None = None
    memo: str = ""


class RevenueRecognitionEntryUpdate(BaseModel):
    """수익인식 전표 수정 요청 스키마."""

    rule_id: str | None = None
    amount: Decimal | None = None
    recognition_date: date | None = None
    memo: str | None = None


class RevenueRecognitionEntry(BaseDocument):
    """수익인식 전표 문서."""

    status: RevenueRecognitionEntryStatus = Field(
        default=RevenueRecognitionEntryStatus.DRAFT,
        description="수익인식 전표 상태",
    )
    rule_id: str = ""
    amount: Decimal = Decimal(0)
    recognition_date: date | None = None
    memo: str = ""
