"""설비가동율(EquipmentAvailability) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class EquipmentAvailabilityCreate(BaseModel):
    """설비가동율 생성 요청 스키마."""

    equipment_id: str
    period_start: date | None = None
    period_end: date | None = None
    total_hours: float = 0.0
    operating_hours: float = 0.0
    downtime_hours: float = 0.0
    planned_downtime_hours: float = 0.0
    unplanned_downtime_hours: float = 0.0
    failure_count: int = 0


class EquipmentAvailabilityUpdate(BaseModel):
    """설비가동율 수정 요청 스키마."""

    equipment_id: str | None = None
    period_start: date | None = None
    period_end: date | None = None
    total_hours: float | None = None
    operating_hours: float | None = None
    downtime_hours: float | None = None
    planned_downtime_hours: float | None = None
    unplanned_downtime_hours: float | None = None
    failure_count: int | None = None
    availability_rate: float | None = None
    mtbf_hours: float | None = None
    mttr_hours: float | None = None


class EquipmentAvailability(BaseDocument):
    """설비가동율 문서."""

    equipment_id: str = ""
    period_start: date | None = None
    period_end: date | None = None
    total_hours: float = 0.0
    operating_hours: float = 0.0
    downtime_hours: float = 0.0
    planned_downtime_hours: float = 0.0
    unplanned_downtime_hours: float = 0.0
    failure_count: int = 0
    availability_rate: float = 0.0
    mtbf_hours: float = 0.0
    mttr_hours: float = 0.0
