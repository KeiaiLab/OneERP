"""예비 부품(SparePart) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SparePartCreate(BaseModel):
    """예비 부품 생성 요청 스키마."""

    part_name: str
    part_code: str = ""
    compatible_assets: list[str] = Field(default_factory=list)
    qty_on_hand: int = 0
    reorder_level: int = 0
    unit_cost: Decimal = Decimal(0)


class SparePartUpdate(BaseModel):
    """예비 부품 수정 요청 스키마."""

    part_name: str | None = None
    part_code: str | None = None
    compatible_assets: list[str] | None = None
    qty_on_hand: int | None = None
    reorder_level: int | None = None
    unit_cost: Decimal | None = None


class SparePart(BaseDocument):
    """예비 부품 문서."""

    part_name: str = ""
    part_code: str = ""
    compatible_assets: list[str] = Field(default_factory=list)
    qty_on_hand: int = 0
    reorder_level: int = 0
    unit_cost: Decimal = Decimal(0)
