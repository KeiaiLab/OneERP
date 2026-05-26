"""공급계획 모델 — 수요 충족을 위한 공급 계획을 관리한다."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class SupplyPlanCreate(BaseModel):
    """공급계획 생성 요청 스키마."""

    plan_name: str
    demand_plan_id: str = ""
    item_code: str = ""
    supplier: str = ""
    warehouse: str = ""
    planned_qty: Decimal = Decimal(0)
    uom: str = ""
    planned_date: date | None = None
    supply_type: str = "purchase"  # purchase/manufacture/transfer
    lead_time_days: int = 0
    description: str = ""


class SupplyPlanUpdate(BaseModel):
    """공급계획 수정 요청 스키마."""

    plan_name: str | None = None
    planned_qty: Decimal | None = None
    planned_date: date | None = None
    status: str | None = None
    description: str | None = None


class SupplyPlan(BaseDocument):
    """공급계획 문서 — 수요 충족을 위한 공급 계획을 저장한다."""

    plan_name: str = ""
    demand_plan_id: str = ""
    item_code: str = ""
    supplier: str = ""
    warehouse: str = ""
    planned_qty: Decimal = Decimal(0)
    actual_qty: Decimal = Decimal(0)
    uom: str = ""
    planned_date: date | None = None
    supply_type: str = "purchase"
    lead_time_days: int = 0
    status: str = "draft"  # draft/confirmed/in_progress/completed/cancelled
    description: str = ""
