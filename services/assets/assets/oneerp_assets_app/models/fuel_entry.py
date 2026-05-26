"""연료 입력(FuelEntry) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class FuelEntryCreate(BaseModel):
    """연료 입력 생성 요청 스키마."""

    vehicle_id: str
    fuel_date: date | None = None
    fuel_type: str = ""
    quantity: Decimal = Decimal(0)
    unit_price: Decimal = Decimal(0)
    total_cost: Decimal = Decimal(0)
    odometer: Decimal = Decimal(0)


class FuelEntryUpdate(BaseModel):
    """연료 입력 수정 요청 스키마."""

    vehicle_id: str | None = None
    fuel_date: date | None = None
    fuel_type: str | None = None
    quantity: Decimal | None = None
    unit_price: Decimal | None = None
    total_cost: Decimal | None = None
    odometer: Decimal | None = None


class FuelEntry(BaseDocument):
    """연료 입력 문서."""

    vehicle_id: str = ""
    fuel_date: date | None = None
    fuel_type: str = ""
    quantity: Decimal = Decimal(0)
    unit_price: Decimal = Decimal(0)
    total_cost: Decimal = Decimal(0)
    odometer: Decimal = Decimal(0)
