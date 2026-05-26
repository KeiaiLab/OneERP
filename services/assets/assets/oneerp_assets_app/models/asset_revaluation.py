"""자산 재평가(AssetRevaluation) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class AssetRevaluationCreate(BaseModel):
    """자산 재평가 생성 요청 스키마."""

    asset_id: str
    revaluation_date: date | None = None
    current_value: Decimal = Decimal(0)
    revalued_amount: Decimal = Decimal(0)
    revaluation_method: str = ""


class AssetRevaluationUpdate(BaseModel):
    """자산 재평가 수정 요청 스키마."""

    asset_id: str | None = None
    revaluation_date: date | None = None
    current_value: Decimal | None = None
    revalued_amount: Decimal | None = None
    revaluation_method: str | None = None


class AssetRevaluation(BaseDocument):
    """자산 재평가 문서."""

    asset_id: str = ""
    revaluation_date: date | None = None
    current_value: Decimal = Decimal(0)
    revalued_amount: Decimal = Decimal(0)
    revaluation_method: str = ""
