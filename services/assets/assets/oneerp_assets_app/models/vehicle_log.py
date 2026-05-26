"""차량 운행 일지(VehicleLog) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class VehicleLogCreate(BaseModel):
    """차량 운행 일지 생성 요청 스키마."""

    vehicle_id: str
    driver_id: str = ""
    log_date: date | None = None
    odometer_start: Decimal = Decimal(0)
    odometer_end: Decimal = Decimal(0)
    distance_km: Decimal = Decimal(0)
    fuel_consumed: Decimal = Decimal(0)
    purpose: str = ""


class VehicleLogUpdate(BaseModel):
    """차량 운행 일지 수정 요청 스키마."""

    vehicle_id: str | None = None
    driver_id: str | None = None
    log_date: date | None = None
    odometer_start: Decimal | None = None
    odometer_end: Decimal | None = None
    distance_km: Decimal | None = None
    fuel_consumed: Decimal | None = None
    purpose: str | None = None


class VehicleLog(BaseDocument):
    """차량 운행 일지 문서."""

    vehicle_id: str = ""
    driver_id: str = ""
    log_date: date | None = None
    odometer_start: Decimal = Decimal(0)
    odometer_end: Decimal = Decimal(0)
    distance_km: Decimal = Decimal(0)
    fuel_consumed: Decimal = Decimal(0)
    purpose: str = ""
