"""생산능력 계획(CapacityPlan) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class CapacityPlanStatus(StrEnum):
    """생산능력 계획 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"


class CapacityPlanCreate(BaseModel):
    """생산능력 계획 생성 요청 스키마."""

    workstation_id: str
    period: str = ""
    available_hours: Decimal = Decimal(0)
    planned_hours: Decimal = Decimal(0)
    utilization_rate: Decimal = Decimal(0)


class CapacityPlanUpdate(BaseModel):
    """생산능력 계획 수정 요청 스키마."""

    workstation_id: str | None = None
    period: str | None = None
    available_hours: Decimal | None = None
    planned_hours: Decimal | None = None
    utilization_rate: Decimal | None = None


class CapacityPlan(BaseDocument):
    """생산능력 계획 문서."""

    status: CapacityPlanStatus = Field(
        default=CapacityPlanStatus.DRAFT,
        description="생산능력 계획 상태",
    )
    workstation_id: str = ""
    period: str = ""
    available_hours: Decimal = Decimal(0)
    planned_hours: Decimal = Decimal(0)
    utilization_rate: Decimal = Decimal(0)
