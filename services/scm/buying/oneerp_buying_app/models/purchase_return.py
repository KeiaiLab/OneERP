"""구매반품(PurchaseReturn) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class PurchaseReturnItem(LineItem):
    """구매반품 라인 아이템."""

    item_code: str
    item_name: str
    qty: Decimal
    rate: Decimal
    amount: Decimal = Decimal(0)


class PurchaseReturnCreate(BaseModel):
    """구매반품 생성 요청 스키마."""

    supplier: str
    return_date: date | None = None
    reason: str = ""
    items: list[PurchaseReturnItem] = []


class PurchaseReturnUpdate(BaseModel):
    """구매반품 수정 요청 스키마."""

    supplier: str | None = None
    return_date: date | None = None
    reason: str | None = None
    items: list[PurchaseReturnItem] | None = None


class PurchaseReturn(BaseDocument):
    """구매반품 문서 — 공급업체에 대한 반품 처리.

    naming prefix: PRT
    """

    supplier: str = ""
    return_date: date | None = None
    reason: str = ""
    items: list[PurchaseReturnItem] = []
    total: Decimal = Decimal(0)
