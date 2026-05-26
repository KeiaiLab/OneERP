"""가격표(PriceList) 마스터 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic model_json_schema 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class PriceListItem(BaseModel):
    """가격표 품목 라인."""

    item_code: str = Field(description="품목 코드")
    item_name: str = Field(default="", description="품목명")
    price: Decimal = Field(default=Decimal(0), description="적용 단가")
    min_qty: Decimal = Field(default=Decimal(1), description="최소 수량 조건")


class PriceListCreate(BaseModel):
    """가격표 생성 요청 스키마."""

    price_list_name: str
    currency: str = "KRW"
    selling: bool = True
    buying: bool = False
    is_active: bool = True
    customer_group: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    items: list[PriceListItem] = []


class PriceListUpdate(BaseModel):
    """가격표 수정 요청 스키마."""

    price_list_name: str | None = None
    currency: str | None = None
    selling: bool | None = None
    buying: bool | None = None
    is_active: bool | None = None
    customer_group: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    items: list[PriceListItem] | None = None


class PriceList(BaseDocument):
    """가격표 마스터 — 판매/구매 가격 목록 관리.

    naming prefix: PLT
    """

    price_list_name: str = ""
    currency: str = "KRW"
    selling: bool = True
    buying: bool = False
    is_active: bool = True
    customer_group: str | None = None
    valid_from: date | None = None
    valid_to: date | None = None
    items: list[PriceListItem] = []
