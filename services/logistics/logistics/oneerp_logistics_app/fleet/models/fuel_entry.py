"""주유 기록(FuelEntry) 문서 모델."""

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


class FuelEntryCreate(BaseModel):
    """주유 기록 생성 요청 스키마."""

    vehicle: str
    entry_date: date
    fuel_type: FuelType
    quantity: Decimal
    amount: Decimal
    odometer: Decimal
    fuel_efficiency: Decimal | None = None
    gas_station: str | None = None


class FuelEntryUpdate(BaseModel):
    """주유 기록 수정 요청 스키마."""

    vehicle: str | None = None
    entry_date: date | None = None
    fuel_type: FuelType | None = None
    quantity: Decimal | None = None
    amount: Decimal | None = None
    odometer: Decimal | None = None
    fuel_efficiency: Decimal | None = None
    gas_station: str | None = None


class FuelEntry(BaseDocument):
    """주유 기록 문서."""

    vehicle: str = ""
    entry_date: date | None = None
    fuel_type: FuelType = FuelType.GASOLINE
    quantity: Decimal = Decimal(0)
    amount: Decimal = Decimal(0)
    odometer: Decimal = Decimal(0)
    fuel_efficiency: Decimal | None = None
    gas_station: str | None = None
