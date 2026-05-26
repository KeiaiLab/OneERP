"""탄소 배출(CarbonEmission) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class CarbonEmissionCreate(BaseModel):
    """탄소 배출 생성 요청 스키마."""

    emission_code: str
    company: str = ""
    source_type: str = ""
    source_name: str = ""
    emission_amount: Decimal = Decimal(0)
    unit: str = "tCO2e"
    measurement_date: date | None = None
    facility: str = ""
    calculation_method: str = ""


class CarbonEmissionUpdate(BaseModel):
    """탄소 배출 수정 요청 스키마."""

    emission_code: str | None = None
    company: str | None = None
    source_type: str | None = None
    source_name: str | None = None
    emission_amount: Decimal | None = None
    unit: str | None = None
    measurement_date: date | None = None
    facility: str | None = None
    calculation_method: str | None = None


class CarbonEmission(BaseDocument):
    """탄소 배출 문서."""

    emission_code: str = ""
    company: str = ""
    source_type: str = ""
    source_name: str = ""
    emission_amount: Decimal = Decimal(0)
    unit: str = "tCO2e"
    measurement_date: date | None = None
    facility: str = ""
    calculation_method: str = ""
