"""적치 위치(BinLocation) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class BinLocationCreate(BaseModel):
    """적치 위치 생성 요청 스키마."""

    warehouse_id: str
    location_code: str
    zone: str = ""
    available_capacity: Decimal = Decimal(0)
    is_active: bool = True


class BinLocationUpdate(BaseModel):
    """적치 위치 수정 요청 스키마."""

    warehouse_id: str | None = None
    location_code: str | None = None
    zone: str | None = None
    available_capacity: Decimal | None = None
    is_active: bool | None = None


class BinLocation(BaseDocument):
    """적치 위치 문서."""

    warehouse_id: str = ""
    location_code: str = ""
    zone: str = ""
    available_capacity: Decimal = Decimal(0)
    is_active: bool = True
