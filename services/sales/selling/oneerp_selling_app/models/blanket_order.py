"""포괄주문(Blanket Order) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class BlanketOrderItem(LineItem):
    """포괄주문 라인 아이템."""

    item_code: str
    item_name: str
    qty: Decimal
    rate: Decimal
    ordered_qty: Decimal = Decimal(0)


class BlanketOrderCreate(BaseModel):
    """포괄주문 생성 요청 스키마."""

    customer: str
    from_date: date | None = None
    to_date: date | None = None
    items: list[BlanketOrderItem] = []


class BlanketOrderUpdate(BaseModel):
    """포괄주문 수정 요청 스키마."""

    customer: str | None = None
    from_date: date | None = None
    to_date: date | None = None
    items: list[BlanketOrderItem] | None = None


class BlanketOrder(BaseDocument):
    """포괄주문 문서 — 장기 계약 기반 주문 관리.

    naming prefix: BLO
    """

    customer: str = ""
    from_date: date | None = None
    to_date: date | None = None
    items: list[BlanketOrderItem] = []
    total: Decimal = Decimal(0)
