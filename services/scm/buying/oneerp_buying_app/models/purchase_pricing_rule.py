"""구매 가격규칙(Purchase Pricing Rule) 마스터 모델.

공급업체별 할인/특별가 자동 적용 규칙을 정의한다.
selling의 PricingRule과 동일한 구조이나 구매 컨텍스트에서 사용된다.
"""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.pricing_rule import BasePricingRule
from pydantic import BaseModel


class PurchasePricingRuleCreate(BaseModel):
    """구매 가격규칙 생성 요청 스키마."""

    rule_name: str
    apply_on: str = "item"
    discount_type: str = "percentage"
    discount_value: Decimal = Decimal(0)
    priority: int = 0
    is_active: bool = True
    supplier: str = ""
    item_code: str = ""
    min_qty: Decimal = Decimal(0)


class PurchasePricingRuleUpdate(BaseModel):
    """구매 가격규칙 수정 요청 스키마."""

    rule_name: str | None = None
    apply_on: str | None = None
    discount_type: str | None = None
    discount_value: Decimal | None = None
    priority: int | None = None
    is_active: bool | None = None
    supplier: str | None = None
    item_code: str | None = None
    min_qty: Decimal | None = None


class PurchasePricingRule(BasePricingRule):
    """구매 가격규칙 마스터 — 구매 할인/가격 자동 적용 규칙.

    naming prefix: PPRC
    """

    supplier: str = ""
