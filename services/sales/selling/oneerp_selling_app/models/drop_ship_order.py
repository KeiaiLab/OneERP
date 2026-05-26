"""직배송 주문(DropShipOrder) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class DropShipOrderCreate(BaseModel):
    """직배송 주문 생성 요청 스키마."""

    sales_order_id: str
    supplier_id: str = ""
    customer_id: str = ""
    item_code: str = ""
    qty: Decimal = Decimal(0)
    delivery_date: date | None = None


class DropShipOrderUpdate(BaseModel):
    """직배송 주문 수정 요청 스키마."""

    sales_order_id: str | None = None
    supplier_id: str | None = None
    customer_id: str | None = None
    item_code: str | None = None
    qty: Decimal | None = None
    delivery_date: date | None = None


class DropShipOrder(BaseDocument):
    """직배송 주문 문서."""

    sales_order_id: str = ""
    supplier_id: str = ""
    customer_id: str = ""
    item_code: str = ""
    qty: Decimal = Decimal(0)
    delivery_date: date | None = None
