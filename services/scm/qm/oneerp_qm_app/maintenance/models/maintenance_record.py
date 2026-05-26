"""보전작업기록(MaintenanceRecord) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class MaintenanceRecordCreate(BaseModel):
    """보전작업기록 생성 요청 스키마."""

    work_order_id: str
    equipment_id: str
    record_date: date | None = None
    maintenance_type: str = ""
    performed_by: str = ""
    description: str = ""
    labor_hours: float = 0.0
    material_cost: Decimal = Decimal(0)
    findings: str = ""
    actions_taken: str = ""


class MaintenanceRecordUpdate(BaseModel):
    """보전작업기록 수정 요청 스키마."""

    work_order_id: str | None = None
    equipment_id: str | None = None
    record_date: date | None = None
    maintenance_type: str | None = None
    performed_by: str | None = None
    description: str | None = None
    labor_hours: float | None = None
    material_cost: Decimal | None = None
    findings: str | None = None
    actions_taken: str | None = None


class MaintenanceRecord(BaseDocument):
    """보전작업기록 문서."""

    work_order_id: str = ""
    equipment_id: str = ""
    record_date: date | None = None
    maintenance_type: str = ""
    performed_by: str = ""
    description: str = ""
    labor_hours: float = 0.0
    material_cost: Decimal = Decimal(0)
    findings: str = ""
    actions_taken: str = ""
