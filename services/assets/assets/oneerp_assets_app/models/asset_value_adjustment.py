"""자산 가치 조정(AssetValueAdjustment) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class AssetValueAdjustmentCreate(BaseModel):
    """자산 가치 조정 생성 요청 스키마."""

    asset_id: str
    adjustment_date: date | None = None
    old_value: Decimal = Decimal(0)
    new_value: Decimal = Decimal(0)
    reason: str = ""


class AssetValueAdjustmentUpdate(BaseModel):
    """자산 가치 조정 수정 요청 스키마."""

    asset_id: str | None = None
    adjustment_date: date | None = None
    old_value: Decimal | None = None
    new_value: Decimal | None = None
    reason: str | None = None


class AssetValueAdjustment(BaseDocument):
    """자산 가치 조정 문서."""

    asset_id: str = ""
    adjustment_date: date | None = None
    old_value: Decimal = Decimal(0)
    new_value: Decimal = Decimal(0)
    reason: str = ""
