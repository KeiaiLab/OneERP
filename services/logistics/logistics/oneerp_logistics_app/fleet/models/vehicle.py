"""차량(Vehicle) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class FuelType(StrEnum):
    """연료 유형."""

    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"
    HYBRID = "hybrid"


class VehicleStatus(StrEnum):
    """차량 상태."""

    ACTIVE = "active"
    IN_MAINTENANCE = "in_maintenance"
    DISPOSED = "disposed"


class VehicleCreate(BaseModel):
    """차량 생성 요청 스키마."""

    vehicle_no: str
    vehicle_name: str
    make: str
    model: str
    year: int
    fuel_type: FuelType
    acquisition_date: date
    acquisition_cost: Decimal
    odometer: Decimal = Decimal(0)
    insurance_expiry: date | None = None
    inspection_expiry: date | None = None
    asset: str | None = None
    status: VehicleStatus = VehicleStatus.ACTIVE
    company: str = ""


class VehicleUpdate(BaseModel):
    """차량 수정 요청 스키마."""

    vehicle_no: str | None = None
    vehicle_name: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    fuel_type: FuelType | None = None
    acquisition_date: date | None = None
    acquisition_cost: Decimal | None = None
    odometer: Decimal | None = None
    insurance_expiry: date | None = None
    inspection_expiry: date | None = None
    asset: str | None = None
    status: VehicleStatus | None = None
    company: str | None = None


class Vehicle(BaseDocument):
    """차량 문서."""

    vehicle_no: str = ""
    vehicle_name: str = ""
    make: str = ""
    model: str = ""
    year: int = 0
    fuel_type: FuelType = FuelType.GASOLINE
    acquisition_date: date | None = None
    acquisition_cost: Decimal = Decimal(0)
    odometer: Decimal = Decimal(0)
    insurance_expiry: date | None = None
    inspection_expiry: date | None = None
    asset: str | None = None
    status: VehicleStatus = VehicleStatus.ACTIVE
    company: str = ""
