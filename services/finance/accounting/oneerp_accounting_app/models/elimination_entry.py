"""내부거래 제거 전표(EliminationEntry) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class EliminationEntryStatus(StrEnum):
    """내부거래 제거 전표 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"


class EliminationEntryCreate(BaseModel):
    """내부거래 제거 전표 생성 요청 스키마."""

    group_id: str
    ic_transaction_id: str
    elimination_amount: Decimal = Decimal(0)
    memo: str = ""


class EliminationEntryUpdate(BaseModel):
    """내부거래 제거 전표 수정 요청 스키마."""

    group_id: str | None = None
    ic_transaction_id: str | None = None
    elimination_amount: Decimal | None = None
    memo: str | None = None


class EliminationEntry(BaseDocument):
    """내부거래 제거 전표 문서."""

    status: EliminationEntryStatus = Field(
        default=EliminationEntryStatus.DRAFT,
        description="내부거래 제거 전표 상태",
    )
    group_id: str = ""
    ic_transaction_id: str = ""
    elimination_amount: Decimal = Decimal(0)
    memo: str = ""
