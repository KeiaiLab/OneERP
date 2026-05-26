"""포장전표(PackingSlip) 모델 정의."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class PackingSlipItem(LineItem):
    """포장전표 라인 아이템."""

    item_code: str
    qty: Decimal
    net_weight: Decimal = Decimal(0)
    gross_weight: Decimal = Decimal(0)


class PackingSlip(BaseDocument):
    """포장전표 트랜잭션 — 출하 포장 기록.

    naming prefix: PS
    """

    delivery_note: str = ""
    items: list[PackingSlipItem] = []


class PackingSlipCreate(BaseModel):
    """포장전표 생성 요청."""

    delivery_note: str = ""
    items: list[PackingSlipItem] = []


class PackingSlipUpdate(BaseModel):
    """포장전표 수정 요청."""

    delivery_note: str | None = None
    items: list[PackingSlipItem] | None = None
