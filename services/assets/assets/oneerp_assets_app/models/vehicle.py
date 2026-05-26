"""차량(Vehicle) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class VehicleCreate(BaseModel):
    """차량 생성 요청 스키마."""

    vehicle_name: str
    license_plate: str = ""
    vehicle_type: str = ""
    make: str = ""
    model: str = ""
    year: int = 0
    fuel_type: str = ""
    is_active: bool = True


class VehicleUpdate(BaseModel):
    """차량 수정 요청 스키마."""

    vehicle_name: str | None = None
    license_plate: str | None = None
    vehicle_type: str | None = None
    make: str | None = None
    model: str | None = None
    year: int | None = None
    fuel_type: str | None = None
    is_active: bool | None = None


class Vehicle(BaseDocument):
    """차량 문서."""

    vehicle_name: str = ""
    license_plate: str = ""
    vehicle_type: str = ""
    make: str = ""
    model: str = ""
    year: int = 0
    fuel_type: str = ""
    is_active: bool = True
