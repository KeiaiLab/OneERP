"""자산 손상(AssetImpairment) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class AssetImpairmentCreate(BaseModel):
    """자산 손상 생성 요청 스키마."""

    asset_id: str
    impairment_date: date | None = None
    carrying_amount: Decimal = Decimal(0)
    recoverable_amount: Decimal = Decimal(0)
    impairment_loss: Decimal = Decimal(0)


class AssetImpairmentUpdate(BaseModel):
    """자산 손상 수정 요청 스키마."""

    asset_id: str | None = None
    impairment_date: date | None = None
    carrying_amount: Decimal | None = None
    recoverable_amount: Decimal | None = None
    impairment_loss: Decimal | None = None


class AssetImpairment(BaseDocument):
    """자산 손상 문서."""

    asset_id: str = ""
    impairment_date: date | None = None
    carrying_amount: Decimal = Decimal(0)
    recoverable_amount: Decimal = Decimal(0)
    impairment_loss: Decimal = Decimal(0)
