"""리오더 규칙(Reorder Level) 모델 — 자동 재발주 기준.

L2 비즈니스 룰 매핑:
- BR-STK-017: 리오더 포인트 (current_qty <= reorder_level 시 자동 발주 트리거)
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ReorderLevelCreate(BaseModel):
    """리오더 규칙 생성 요청 스키마."""

    item_code: str
    warehouse: str
    reorder_level: Decimal = Decimal(0)
    reorder_qty: Decimal = Decimal(0)
    material_request_type: str = "purchase"


class ReorderLevelUpdate(BaseModel):
    """리오더 규칙 수정 요청 스키마."""

    item_code: str | None = None
    warehouse: str | None = None
    reorder_level: Decimal | None = None
    reorder_qty: Decimal | None = None
    material_request_type: str | None = None


class ReorderLevel(BaseDocument):
    """리오더 규칙 — 품목별 최소 재고 수준과 재발주 수량.

    재고가 reorder_level 이하로 떨어지면 구매요청을 자동 생성한다.
    naming prefix: ROL
    """

    item_code: str = ""
    warehouse: str = ""
    reorder_level: Decimal = Decimal(0)
    reorder_qty: Decimal = Decimal(0)
    material_request_type: str = "purchase"
