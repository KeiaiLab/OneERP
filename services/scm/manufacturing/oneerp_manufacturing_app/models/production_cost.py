"""생산원가(ProductionCost) 리포트 모델 정의."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class ProductionCost(BaseModel):
    """생산원가 리포트 — 읽기 전용."""

    item_code: str = ""
    item_name: str = ""
    material_cost: Decimal = Decimal(0)
    labour_cost: Decimal = Decimal(0)
    overhead_cost: Decimal = Decimal(0)
    total_cost: Decimal = Decimal(0)
    work_order: str = ""
