"""차량 유지보수(VehicleMaintenance) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class VehicleMaintenanceCreate(BaseModel):
    """차량 유지보수 생성 요청 스키마."""

    vehicle_id: str
    maintenance_type: str = ""
    maintenance_date: date | None = None
    cost: Decimal = Decimal(0)
    next_maintenance_date: date | None = None


class VehicleMaintenanceUpdate(BaseModel):
    """차량 유지보수 수정 요청 스키마."""

    vehicle_id: str | None = None
    maintenance_type: str | None = None
    maintenance_date: date | None = None
    cost: Decimal | None = None
    next_maintenance_date: date | None = None


class VehicleMaintenance(BaseDocument):
    """차량 유지보수 문서."""

    vehicle_id: str = ""
    maintenance_type: str = ""
    maintenance_date: date | None = None
    cost: Decimal = Decimal(0)
    next_maintenance_date: date | None = None
