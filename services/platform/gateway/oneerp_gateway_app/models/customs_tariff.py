"""관세 정보(CustomsTariff) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CustomsTariffCreate(BaseModel):
    """관세 정보 생성 요청 스키마."""

    hs_code: str
    description: str = ""
    tariff_rate: Decimal = Decimal(0)
    country_of_origin: str = ""
    is_active: bool = True


class CustomsTariffUpdate(BaseModel):
    """관세 정보 수정 요청 스키마."""

    hs_code: str | None = None
    description: str | None = None
    tariff_rate: Decimal | None = None
    country_of_origin: str | None = None
    is_active: bool | None = None


class CustomsTariff(BaseDocument):
    """관세 정보 문서."""

    hs_code: str = ""
    description: str = ""
    tariff_rate: Decimal = Decimal(0)
    country_of_origin: str = ""
    is_active: bool = True
