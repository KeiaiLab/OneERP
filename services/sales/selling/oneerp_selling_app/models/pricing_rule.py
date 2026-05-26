"""가격규칙(Pricing Rule) 마스터 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.pricing_rule import BasePricingRule
from pydantic import BaseModel


class PricingRuleCreate(BaseModel):
    """가격규칙 생성 요청 스키마."""

    rule_name: str
    apply_on: str = "item"
    discount_type: str = "percentage"
    discount_value: Decimal = Decimal(0)
    priority: int = 0
    is_active: bool = True


class PricingRuleUpdate(BaseModel):
    """가격규칙 수정 요청 스키마."""

    rule_name: str | None = None
    apply_on: str | None = None
    discount_type: str | None = None
    discount_value: Decimal | None = None
    priority: int | None = None
    is_active: bool | None = None


class PricingRule(BasePricingRule):
    """가격규칙 마스터 — 할인/가격 자동 적용 규칙.

    naming prefix: PRC
    """
