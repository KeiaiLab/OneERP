"""탄소 배출(CarbonEmission) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CarbonEmissionCreate(BaseModel):
    """탄소 배출 생성 요청 스키마."""

    scope: str
    source: str = ""
    emission_amount: Decimal = Decimal(0)
    unit: str = "tCO2e"
    period: str = ""


class CarbonEmissionUpdate(BaseModel):
    """탄소 배출 수정 요청 스키마."""

    scope: str | None = None
    source: str | None = None
    emission_amount: Decimal | None = None
    unit: str | None = None
    period: str | None = None


class CarbonEmission(BaseDocument):
    """탄소 배출 문서."""

    scope: str = ""
    source: str = ""
    emission_amount: Decimal = Decimal(0)
    unit: str = "tCO2e"
    period: str = ""
