"""마켓플레이스 주문(MarketplaceOrder) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class MarketplaceOrderCreate(BaseModel):
    """마켓플레이스 주문 생성 요청 스키마."""

    marketplace: str
    external_order_id: str = ""
    customer_name: str = ""
    total_amount: Decimal = Decimal(0)
    order_date: date | None = None


class MarketplaceOrderUpdate(BaseModel):
    """마켓플레이스 주문 수정 요청 스키마."""

    marketplace: str | None = None
    external_order_id: str | None = None
    customer_name: str | None = None
    total_amount: Decimal | None = None
    order_date: date | None = None


class MarketplaceOrder(BaseDocument):
    """마켓플레이스 주문 문서."""

    marketplace: str = ""
    external_order_id: str = ""
    customer_name: str = ""
    total_amount: Decimal = Decimal(0)
    order_date: date | None = None
