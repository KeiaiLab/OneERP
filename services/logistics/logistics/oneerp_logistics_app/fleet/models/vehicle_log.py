"""운행 기록(VehicleLog) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class VehicleLogCreate(BaseModel):
    """운행 기록 생성 요청 스키마."""

    vehicle: str
    driver: str
    log_date: date
    start_odometer: Decimal
    end_odometer: Decimal
    distance: Decimal
    purpose: str
    destination: str | None = None


class VehicleLogUpdate(BaseModel):
    """운행 기록 수정 요청 스키마."""

    vehicle: str | None = None
    driver: str | None = None
    log_date: date | None = None
    start_odometer: Decimal | None = None
    end_odometer: Decimal | None = None
    distance: Decimal | None = None
    purpose: str | None = None
    destination: str | None = None


class VehicleLog(BaseDocument):
    """운행 기록 문서."""

    vehicle: str = ""
    driver: str = ""
    log_date: date | None = None
    start_odometer: Decimal = Decimal(0)
    end_odometer: Decimal = Decimal(0)
    distance: Decimal = Decimal(0)
    purpose: str = ""
    destination: str | None = None
