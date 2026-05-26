"""안전재고 규칙(SafetyStockRule) 문서 모델.

L2 비즈니스 룰 매핑:
- BR-STK-016: 안전재고 알림 (current_qty < safety_stock_qty 시 알림)
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SafetyStockRuleCreate(BaseModel):
    """안전재고 규칙 생성 요청 스키마."""

    item_code: str
    warehouse_id: str
    minimum_qty: Decimal = Decimal(0)
    reorder_qty: Decimal = Decimal(0)
    lead_days: int = 0


class SafetyStockRuleUpdate(BaseModel):
    """안전재고 규칙 수정 요청 스키마."""

    item_code: str | None = None
    warehouse_id: str | None = None
    minimum_qty: Decimal | None = None
    reorder_qty: Decimal | None = None
    lead_days: int | None = None


class SafetyStockRule(BaseDocument):
    """안전재고 규칙 문서."""

    item_code: str = ""
    warehouse_id: str = ""
    minimum_qty: Decimal = Decimal(0)
    reorder_qty: Decimal = Decimal(0)
    lead_days: int = 0
