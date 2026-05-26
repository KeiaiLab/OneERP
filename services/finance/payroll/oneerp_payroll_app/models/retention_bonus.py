"""리텐션 보너스(RetentionBonus) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class RetentionBonusStatus(StrEnum):
    """유지 보너스 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class RetentionBonusCreate(BaseModel):
    """리텐션 보너스 생성 요청 스키마."""

    employee_id: str
    bonus_amount: Decimal = Decimal(0)
    retention_period_months: int = 0
    payment_date: date | None = None
    contract_end: date | None = None


class RetentionBonusUpdate(BaseModel):
    """리텐션 보너스 수정 요청 스키마."""

    employee_id: str | None = None
    bonus_amount: Decimal | None = None
    retention_period_months: int | None = None
    payment_date: date | None = None
    contract_end: date | None = None
    status: RetentionBonusStatus | None = None


class RetentionBonus(BaseDocument):
    """리텐션 보너스 문서."""

    status: RetentionBonusStatus = Field(
        default=RetentionBonusStatus.DRAFT,
        description="유지 보너스 상태",
    )
    employee_id: str = ""
    bonus_amount: Decimal = Decimal(0)
    retention_period_months: int = 0
    payment_date: date | None = None
    contract_end: date | None = None
