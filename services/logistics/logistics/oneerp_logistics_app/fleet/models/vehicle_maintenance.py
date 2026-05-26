"""차량 정비(VehicleMaintenance) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class MaintenanceType(StrEnum):
    """정비 유형."""

    REGULAR = "regular"
    REPAIR = "repair"
    INSPECTION = "inspection"
    TIRE = "tire"
    OIL_CHANGE = "oil_change"


class MaintenanceStatus(StrEnum):
    """정비 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    COMPLETED = "completed"


class VehicleMaintenanceCreate(BaseModel):
    """차량 정비 생성 요청 스키마."""

    vehicle: str
    maintenance_type: MaintenanceType
    maintenance_date: date
    description: str
    cost: Decimal
    vendor: str | None = None
    next_due_date: date | None = None
    next_due_odometer: Decimal | None = None
    status: MaintenanceStatus = MaintenanceStatus.DRAFT


class VehicleMaintenanceUpdate(BaseModel):
    """차량 정비 수정 요청 스키마."""

    vehicle: str | None = None
    maintenance_type: MaintenanceType | None = None
    maintenance_date: date | None = None
    description: str | None = None
    cost: Decimal | None = None
    vendor: str | None = None
    next_due_date: date | None = None
    next_due_odometer: Decimal | None = None
    status: MaintenanceStatus | None = None


class VehicleMaintenance(BaseDocument):
    """차량 정비 문서."""

    vehicle: str = ""
    maintenance_type: MaintenanceType = MaintenanceType.REGULAR
    maintenance_date: date | None = None
    description: str = ""
    cost: Decimal = Decimal(0)
    vendor: str | None = None
    next_due_date: date | None = None
    next_due_odometer: Decimal | None = None
    status: MaintenanceStatus = MaintenanceStatus.DRAFT
