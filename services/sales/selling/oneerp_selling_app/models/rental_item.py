"""렌탈 품목(RentalItem) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class RentalItemCreate(BaseModel):
    """렌탈 품목 생성 요청 스키마."""

    item_code: str
    item_name: str = ""
    daily_rate: Decimal = Decimal(0)
    is_available: bool = True
    condition: str = ""


class RentalItemUpdate(BaseModel):
    """렌탈 품목 수정 요청 스키마."""

    item_code: str | None = None
    item_name: str | None = None
    daily_rate: Decimal | None = None
    is_available: bool | None = None
    condition: str | None = None


class RentalItem(BaseDocument):
    """렌탈 품목 문서."""

    item_code: str = ""
    item_name: str = ""
    daily_rate: Decimal = Decimal(0)
    is_available: bool = True
    condition: str = ""
