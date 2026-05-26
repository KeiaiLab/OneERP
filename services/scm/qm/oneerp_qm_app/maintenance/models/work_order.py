"""작업지시(WorkOrder) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date, datetime


class WorkOrderStatus(StrEnum):
    """작업지시 상태."""

    DRAFT = "draft"
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class WorkOrderPriority(StrEnum):
    """작업지시 우선순위."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SparePartUsage(BaseModel):
    """작업지시에서 사용한 예비자재."""

    spare_part_id: str = ""
    part_name: str = ""
    qty_used: int = 0
    unit_cost: Decimal = Decimal(0)


class WorkOrderCreate(BaseModel):
    """작업지시 생성 요청 스키마."""

    equipment_id: str
    title: str
    work_order_type: str = "corrective"
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    assigned_to: str = ""
    assigned_team: str = ""
    scheduled_date: date | None = None
    due_date: date | None = None
    description: str = ""
    breakdown_report_id: str = ""
    pm_plan_id: str = ""


class WorkOrderUpdate(BaseModel):
    """작업지시 수정 요청 스키마."""

    equipment_id: str | None = None
    title: str | None = None
    work_order_type: str | None = None
    priority: WorkOrderPriority | None = None
    status: WorkOrderStatus | None = None
    assigned_to: str | None = None
    assigned_team: str | None = None
    scheduled_date: date | None = None
    due_date: date | None = None
    description: str | None = None
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    labor_hours: float | None = None
    material_cost: Decimal | None = None
    labor_cost: Decimal | None = None
    root_cause: str | None = None
    resolution: str | None = None
    spare_parts_used: list[SparePartUsage] | None = None


class WorkOrder(BaseDocument):
    """작업지시 문서."""

    equipment_id: str = ""
    title: str = ""
    work_order_type: str = "corrective"
    priority: WorkOrderPriority = WorkOrderPriority.MEDIUM
    status: WorkOrderStatus = WorkOrderStatus.DRAFT
    assigned_to: str = ""
    assigned_team: str = ""
    scheduled_date: date | None = None
    due_date: date | None = None
    description: str = ""
    breakdown_report_id: str = ""
    pm_plan_id: str = ""
    actual_start: datetime | None = None
    actual_end: datetime | None = None
    labor_hours: float = 0.0
    material_cost: Decimal = Decimal(0)
    labor_cost: Decimal = Decimal(0)
    total_cost: Decimal = Decimal(0)
    root_cause: str = ""
    resolution: str = ""
    spare_parts_used: list[SparePartUsage] = Field(default_factory=list)
