"""폐기물 관리(WasteManagement) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class WasteManagementCreate(BaseModel):
    """폐기물 관리 생성 요청 스키마."""

    waste_type: str
    quantity: Decimal = Decimal(0)
    unit: str = "kg"
    disposal_method: str = ""
    disposal_date: date | None = None


class WasteManagementUpdate(BaseModel):
    """폐기물 관리 수정 요청 스키마."""

    waste_type: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    disposal_method: str | None = None
    disposal_date: date | None = None


class WasteManagement(BaseDocument):
    """폐기물 관리 문서."""

    waste_type: str = ""
    quantity: Decimal = Decimal(0)
    unit: str = "kg"
    disposal_method: str = ""
    disposal_date: date | None = None
