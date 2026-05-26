"""드롭쉬핑 주문 모델 — 공급업체 직배송 주문을 관리한다."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class DropShipItem(BaseModel):
    """드롭쉬핑 주문 품목."""

    item_code: str = ""
    item_name: str = ""
    qty: int = 0
    price: Decimal = Decimal(0)


class DropShipOrderCreate(BaseModel):
    """드롭쉬핑 주문 생성 요청 스키마."""

    sales_order_id: str
    supplier_id: str
    items: list[DropShipItem] = []
    shipping_address: str = ""
    status: str = "draft"


class DropShipOrderUpdate(BaseModel):
    """드롭쉬핑 주문 수정 요청 스키마."""

    status: str | None = None
    tracking_number: str | None = None
    shipping_address: str | None = None


class DropShipOrder(BaseDocument):
    """드롭쉬핑 주문 문서 — 공급업체 직배송 주문 정보를 저장한다."""

    sales_order_id: str = ""
    supplier_id: str = ""
    items: list[DropShipItem] = []
    shipping_address: str = ""
    status: str = "draft"  # draft/submitted/shipped/delivered
    tracking_number: str = ""
