"""자산처분(AssetDisposal) 문서 모델 — Assets 모듈."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class AssetDisposalCreate(BaseModel):
    """자산처분 생성 요청 스키마."""

    asset: str
    asset_name: str = ""
    disposal_date: date | None = None
    disposal_method: str = "sale"
    sale_amount: Decimal = Decimal(0)
    book_value: Decimal = Decimal(0)
    gain_loss: Decimal = Decimal(0)


class AssetDisposalUpdate(BaseModel):
    """자산처분 수정 요청 스키마."""

    asset: str | None = None
    asset_name: str | None = None
    disposal_date: date | None = None
    disposal_method: str | None = None
    sale_amount: Decimal | None = None
    book_value: Decimal | None = None
    gain_loss: Decimal | None = None


class AssetDisposal(BaseDocument):
    """자산처분 문서 — Assets 자산처분 트랜잭션.

    naming prefix: ADSP
    """

    asset: str = ""
    asset_name: str = ""
    disposal_date: date | None = None
    disposal_method: str = "sale"
    sale_amount: Decimal = Decimal(0)
    book_value: Decimal = Decimal(0)
    gain_loss: Decimal = Decimal(0)
