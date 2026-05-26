"""구독 플랜(SubscriptionPlan) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SubscriptionPlanCreate(BaseModel):
    """구독 플랜 생성 요청 스키마."""

    plan_name: str
    billing_interval: str = ""
    price: Decimal = Decimal(0)
    currency: str = "KRW"
    features: list[str] = Field(default_factory=list)
    is_active: bool = True


class SubscriptionPlanUpdate(BaseModel):
    """구독 플랜 수정 요청 스키마."""

    plan_name: str | None = None
    billing_interval: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    features: list[str] | None = None
    is_active: bool | None = None


class SubscriptionPlan(BaseDocument):
    """구독 플랜 문서."""

    plan_name: str = ""
    billing_interval: str = ""
    price: Decimal = Decimal(0)
    currency: str = "KRW"
    features: list[str] = Field(default_factory=list)
    is_active: bool = True
