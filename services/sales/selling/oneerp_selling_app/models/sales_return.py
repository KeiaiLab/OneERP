"""판매반품(Sales Return) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class SalesReturnItem(LineItem):
    """판매반품 라인 아이템."""

    item_code: str
    item_name: str
    qty: Decimal
    rate: Decimal
    amount: Decimal = Decimal(0)


class SalesReturnCreate(BaseModel):
    """판매반품 생성 요청 스키마."""

    customer: str
    return_date: date | None = None
    reason: str = ""
    items: list[SalesReturnItem] = []


class SalesReturnUpdate(BaseModel):
    """판매반품 수정 요청 스키마."""

    customer: str | None = None
    return_date: date | None = None
    reason: str | None = None
    items: list[SalesReturnItem] | None = None


class SalesReturn(BaseDocument):
    """판매반품 문서 — 고객으로부터 반품 처리.

    naming prefix: SRT
    """

    customer: str = ""
    return_date: date | None = None
    reason: str = ""
    items: list[SalesReturnItem] = []
    total: Decimal = Decimal(0)
