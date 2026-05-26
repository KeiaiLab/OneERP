"""마켓플레이스 주문 모델 — 외부 마켓플레이스에서 동기화된 주문을 관리한다."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class MarketplaceOrderItem(BaseModel):
    """마켓플레이스 주문 품목."""

    item_code: str = ""
    item_name: str = ""
    qty: int = 0
    price: Decimal = Decimal(0)


class MarketplaceOrderCreate(BaseModel):
    """마켓플레이스 주문 생성 요청 스키마."""

    channel_id: str
    external_order_id: str
    customer_name: str
    items: list[MarketplaceOrderItem] = []
    total_amount: Decimal = Decimal(0)
    status: str = "synced"


class MarketplaceOrderUpdate(BaseModel):
    """마켓플레이스 주문 수정 요청 스키마."""

    status: str | None = None
    sales_order_id: str | None = None
    customer_name: str | None = None


class MarketplaceOrder(BaseDocument):
    """마켓플레이스 주문 문서 — 외부 플랫폼에서 동기화된 주문을 저장한다."""

    channel_id: str = ""
    external_order_id: str = ""
    customer_name: str = ""
    items: list[MarketplaceOrderItem] = []
    total_amount: Decimal = Decimal(0)
    status: str = "synced"  # synced/confirmed/fulfilled/cancelled
    sales_order_id: str = ""
    synced_at: datetime | None = None
