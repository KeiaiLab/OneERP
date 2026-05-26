"""생산능력계획 모델 — 생산 자원의 가용 능력을 계획한다."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class CapacityPlanCreate(BaseModel):
    """생산능력계획 생성 요청 스키마."""

    plan_name: str
    workstation: str = ""
    resource_type: str = "machine"  # machine/labor/tool
    period_start: date | None = None
    period_end: date | None = None
    available_hours: Decimal = Decimal(0)
    planned_hours: Decimal = Decimal(0)
    description: str = ""


class CapacityPlanUpdate(BaseModel):
    """생산능력계획 수정 요청 스키마."""

    plan_name: str | None = None
    available_hours: Decimal | None = None
    planned_hours: Decimal | None = None
    actual_hours: Decimal | None = None
    status: str | None = None
    description: str | None = None


class CapacityPlan(BaseDocument):
    """생산능력계획 문서 — 생산 자원 가용 능력 정보를 저장한다."""

    plan_name: str = ""
    workstation: str = ""
    resource_type: str = "machine"
    period_start: date | None = None
    period_end: date | None = None
    available_hours: Decimal = Decimal(0)
    planned_hours: Decimal = Decimal(0)
    actual_hours: Decimal = Decimal(0)
    utilization_percent: Decimal = Decimal(0)
    status: str = "draft"  # draft/active/closed
    description: str = ""
