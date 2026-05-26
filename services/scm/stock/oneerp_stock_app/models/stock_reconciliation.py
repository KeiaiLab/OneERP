"""재고조정(StockReconciliation) 모델 정의."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class StockReconciliationItem(LineItem):
    """재고조정 라인 아이템."""

    item_code: str
    warehouse: str
    qty: Decimal
    valuation_rate: Decimal = Decimal(0)
    current_qty: Decimal = Decimal(0)


class StockReconciliation(BaseDocument):
    """재고조정 문서 — 실사 기반 재고 보정.

    naming prefix: SREC
    """

    posting_date: date | None = None
    purpose: str = "stock_reconciliation"
    items: list[StockReconciliationItem] = []


class StockReconciliationCreate(BaseModel):
    """재고조정 생성 요청."""

    posting_date: date | None = None
    purpose: str = "stock_reconciliation"
    items: list[StockReconciliationItem] = []


class StockReconciliationUpdate(BaseModel):
    """재고조정 수정 요청."""

    posting_date: date | None = None
    purpose: str | None = None
    items: list[StockReconciliationItem] | None = None
