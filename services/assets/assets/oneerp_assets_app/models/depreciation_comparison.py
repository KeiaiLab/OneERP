"""감가상각 비교(DepreciationComparison) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class DepreciationComparisonCreate(BaseModel):
    """감가상각 비교 생성 요청 스키마."""

    asset_id: str
    method_1: str = ""
    method_2: str = ""
    amount_1: Decimal = Decimal(0)
    amount_2: Decimal = Decimal(0)
    difference: Decimal = Decimal(0)


class DepreciationComparisonUpdate(BaseModel):
    """감가상각 비교 수정 요청 스키마."""

    asset_id: str | None = None
    method_1: str | None = None
    method_2: str | None = None
    amount_1: Decimal | None = None
    amount_2: Decimal | None = None
    difference: Decimal | None = None


class DepreciationComparison(BaseDocument):
    """감가상각 비교 문서."""

    asset_id: str = ""
    method_1: str = ""
    method_2: str = ""
    amount_1: Decimal = Decimal(0)
    amount_2: Decimal = Decimal(0)
    difference: Decimal = Decimal(0)
