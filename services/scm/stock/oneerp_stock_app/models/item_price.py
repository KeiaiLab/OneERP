"""품목가격(ItemPrice) 모델 정의."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ItemPrice(BaseDocument):
    """품목가격 마스터 — 가격표별 품목 가격.

    naming prefix: IPR
    """

    item_code: str = ""
    price_list: str = ""
    price: Decimal = Decimal(0)
    currency: str = "KRW"
    min_qty: Decimal = Decimal(0)


class ItemPriceCreate(BaseModel):
    """품목가격 생성 요청."""

    item_code: str = ""
    price_list: str = ""
    price: Decimal = Decimal(0)
    currency: str = "KRW"
    min_qty: Decimal = Decimal(0)


class ItemPriceUpdate(BaseModel):
    """품목가격 수정 요청."""

    item_code: str | None = None
    price_list: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    min_qty: Decimal | None = None
