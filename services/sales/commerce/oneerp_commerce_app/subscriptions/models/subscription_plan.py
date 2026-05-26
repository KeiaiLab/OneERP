"""구독 플랜 모델 — SaaS/정기 서비스의 플랜을 관리한다."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SubscriptionPlanCreate(BaseModel):
    """구독 플랜 생성 요청 스키마."""

    plan_name: str
    billing_interval: str  # monthly/quarterly/yearly
    price: Decimal = Decimal(0)
    currency: str = "KRW"
    features: list[str] = []
    trial_days: int = 0
    is_active: bool = True
    company: str = ""


class SubscriptionPlanUpdate(BaseModel):
    """구독 플랜 수정 요청 스키마."""

    plan_name: str | None = None
    billing_interval: str | None = None
    price: Decimal | None = None
    currency: str | None = None
    features: list[str] | None = None
    trial_days: int | None = None
    is_active: bool | None = None


class SubscriptionPlan(BaseDocument):
    """구독 플랜 문서 — 플랜 정보를 저장한다."""

    plan_name: str = ""
    billing_interval: str = "monthly"  # monthly/quarterly/yearly
    price: Decimal = Decimal(0)
    currency: str = "KRW"
    features: list[str] = []
    trial_days: int = 0
    is_active: bool = True
    company: str = ""
