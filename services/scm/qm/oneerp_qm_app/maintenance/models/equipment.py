"""설비(Equipment) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class EquipmentStatus(StrEnum):
    """설비 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    UNDER_MAINTENANCE = "under_maintenance"
    DECOMMISSIONED = "decommissioned"


class EquipmentCreate(BaseModel):
    """설비 생성 요청 스키마."""

    equipment_name: str
    equipment_code: str = ""
    category: str = ""
    location: str = ""
    manufacturer: str = ""
    model_number: str = ""
    serial_number: str = ""
    installation_date: date | None = None
    purchase_cost: Decimal = Decimal(0)
    status: EquipmentStatus = EquipmentStatus.ACTIVE
    criticality: str = "medium"
    description: str = ""


class EquipmentUpdate(BaseModel):
    """설비 수정 요청 스키마."""

    equipment_name: str | None = None
    equipment_code: str | None = None
    category: str | None = None
    location: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    serial_number: str | None = None
    installation_date: date | None = None
    purchase_cost: Decimal | None = None
    status: EquipmentStatus | None = None
    criticality: str | None = None
    description: str | None = None


class Equipment(BaseDocument):
    """설비 문서."""

    equipment_name: str = ""
    equipment_code: str = ""
    category: str = ""
    location: str = ""
    manufacturer: str = ""
    model_number: str = ""
    serial_number: str = ""
    installation_date: date | None = None
    purchase_cost: Decimal = Decimal(0)
    status: EquipmentStatus = EquipmentStatus.ACTIVE
    criticality: str = "medium"
    description: str = ""
    total_downtime_hours: float = 0.0
    mtbf_hours: float = 0.0
    mttr_hours: float = 0.0
    failure_count: int = 0
    tags: list[str] = Field(default_factory=list)
