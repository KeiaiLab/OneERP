"""자산분류(AssetCategory) 문서 모델 — Assets 모듈."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AssetCategoryCreate(BaseModel):
    """자산분류 생성 요청 스키마."""

    category_name: str
    depreciation_method: str = "straight_line"
    useful_life_years: int = 5
    depreciation_rate: Decimal = Decimal(0)


class AssetCategoryUpdate(BaseModel):
    """자산분류 수정 요청 스키마."""

    category_name: str | None = None
    depreciation_method: str | None = None
    useful_life_years: int | None = None
    depreciation_rate: Decimal | None = None


class AssetCategory(BaseDocument):
    """자산분류 문서 — Assets 자산분류 마스터.

    naming prefix: ACAT
    """

    category_name: str = ""
    depreciation_method: str = "straight_line"
    useful_life_years: int = 5
    depreciation_rate: Decimal = Decimal(0)
