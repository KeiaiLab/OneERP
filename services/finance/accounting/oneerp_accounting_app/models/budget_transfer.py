"""예산 전용(BudgetTransfer) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class BudgetTransferStatus(StrEnum):
    """예산 전용 상태."""

    DRAFT = "draft"
    APPROVED = "approved"
    EXECUTED = "executed"


class BudgetTransferCreate(BaseModel):
    """예산 전용 생성 요청 스키마."""

    from_budget_id: str
    to_budget_id: str
    transfer_amount: Decimal = Decimal(0)
    transfer_date: date | None = None
    reason: str = ""


class BudgetTransferUpdate(BaseModel):
    """예산 전용 수정 요청 스키마."""

    from_budget_id: str | None = None
    to_budget_id: str | None = None
    transfer_amount: Decimal | None = None
    transfer_date: date | None = None
    reason: str | None = None


class BudgetTransfer(BaseDocument):
    """예산 전용 문서."""

    status: BudgetTransferStatus = Field(
        default=BudgetTransferStatus.DRAFT,
        description="예산 전용 상태",
    )
    from_budget_id: str = ""
    to_budget_id: str = ""
    transfer_amount: Decimal = Decimal(0)
    transfer_date: date | None = None
    reason: str = ""
