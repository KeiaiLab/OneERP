"""피킹목록(PickList) 모델 정의."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class PickListItem(LineItem):
    """피킹목록 라인 아이템."""

    item_code: str
    qty: Decimal
    warehouse: str
    picked_qty: Decimal = Decimal(0)


class PickList(BaseDocument):
    """피킹목록 트랜잭션 — 출고 피킹 지시.

    naming prefix: PL
    """

    purpose: str = "delivery"
    items: list[PickListItem] = []


class PickListCreate(BaseModel):
    """피킹목록 생성 요청."""

    purpose: str = "delivery"
    items: list[PickListItem] = []


class PickListUpdate(BaseModel):
    """피킹목록 수정 요청."""

    purpose: str | None = None
    items: list[PickListItem] | None = None
