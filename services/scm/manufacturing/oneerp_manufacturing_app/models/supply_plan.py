"""공급 계획(SupplyPlan) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class SupplyPlanStatus(StrEnum):
    """공급 계획 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPLIED = "applied"


class SupplyPlanCreate(BaseModel):
    """공급 계획 생성 요청 스키마."""

    item_code: str
    planned_qty: Decimal = Decimal(0)
    source_type: str = ""
    planned_start: date | None = None
    planned_end: date | None = None


class SupplyPlanUpdate(BaseModel):
    """공급 계획 수정 요청 스키마."""

    item_code: str | None = None
    planned_qty: Decimal | None = None
    source_type: str | None = None
    planned_start: date | None = None
    planned_end: date | None = None


class SupplyPlan(BaseDocument):
    """공급 계획 문서."""

    status: SupplyPlanStatus = Field(
        default=SupplyPlanStatus.DRAFT,
        description="공급 계획 상태",
    )
    item_code: str = ""
    planned_qty: Decimal = Decimal(0)
    source_type: str = ""
    planned_start: date | None = None
    planned_end: date | None = None
