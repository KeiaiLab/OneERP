"""자산(Asset) 문서 모델 — Assets 모듈.

L2 비즈니스 룰: BR-001 (Draft만 수정), BR-002 (Draft만 삭제), BR-003 (Submitted만 폐기),
BR-014 (문서 제출 상태 검증), BR-015 (문서 취소 상태 검증), BR-017 (자산 존재 확인).
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class DepreciationMethod(StrEnum):
    """감가상각 방법."""

    STRAIGHT_LINE = "straight_line"
    DECLINING_BALANCE = "declining_balance"


class AssetStatus(StrEnum):
    """자산 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    SCRAPPED = "scrapped"


class AssetCreate(BaseModel):
    """자산 생성 요청 스키마."""

    asset_name: str
    asset_category: str = ""
    purchase_date: date | None = None
    gross_amount: Decimal = Decimal(0)
    depreciation_method: DepreciationMethod = DepreciationMethod.STRAIGHT_LINE
    useful_life_years: int = 0
    salvage_value: Decimal = Decimal(0)
    current_value: Decimal = Decimal(0)


class AssetUpdate(BaseModel):
    """자산 수정 요청 스키마."""

    asset_name: str | None = None
    asset_category: str | None = None
    purchase_date: date | None = None
    gross_amount: Decimal | None = None
    depreciation_method: DepreciationMethod | None = None
    useful_life_years: int | None = None
    salvage_value: Decimal | None = None
    current_value: Decimal | None = None


class Asset(BaseDocument):
    """자산 문서 — Assets 자산 관리.

    naming prefix: ASSET
    """

    asset_name: str = ""
    asset_category: str = ""
    purchase_date: date | None = None
    gross_amount: Decimal = Decimal(0)
    depreciation_method: DepreciationMethod = DepreciationMethod.STRAIGHT_LINE
    useful_life_years: int = 0
    salvage_value: Decimal = Decimal(0)
    current_value: Decimal = Decimal(0)
    status: AssetStatus = AssetStatus.DRAFT
