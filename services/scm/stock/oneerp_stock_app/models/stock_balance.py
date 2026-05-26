"""재고잔액(StockBalance) 리포트 모델 정의."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class StockBalance(BaseModel):
    """재고잔액 리포트 — 읽기 전용."""

    item_code: str = ""
    item_name: str = ""
    warehouse: str = ""
    actual_qty: Decimal = Decimal(0)
    valuation_rate: Decimal = Decimal(0)
    stock_value: Decimal = Decimal(0)
