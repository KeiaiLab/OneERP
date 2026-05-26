"""연결 조정 전표(ConsolidationEntry) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ConsolidationEntryStatus(StrEnum):
    """연결 조정 전표 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    FINALIZED = "finalized"


class ConsolidationEntryCreate(BaseModel):
    """연결 조정 전표 생성 요청 스키마."""

    group_id: str
    period: str
    total_debit: Decimal = Decimal(0)
    total_credit: Decimal = Decimal(0)
    memo: str = ""


class ConsolidationEntryUpdate(BaseModel):
    """연결 조정 전표 수정 요청 스키마."""

    group_id: str | None = None
    period: str | None = None
    total_debit: Decimal | None = None
    total_credit: Decimal | None = None
    memo: str | None = None


class ConsolidationEntry(BaseDocument):
    """연결 조정 전표 문서."""

    status: ConsolidationEntryStatus = Field(
        default=ConsolidationEntryStatus.DRAFT,
        description="연결 조정 전표 상태",
    )
    group_id: str = ""
    period: str = ""
    total_debit: Decimal = Decimal(0)
    total_credit: Decimal = Decimal(0)
    memo: str = ""
