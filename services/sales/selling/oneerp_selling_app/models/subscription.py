"""구독(Subscription) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SubscriptionCreate(BaseModel):
    """구독 생성 요청 스키마."""

    customer_id: str
    plan_id: str = ""
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool = True
    auto_renew: bool = True


class SubscriptionUpdate(BaseModel):
    """구독 수정 요청 스키마."""

    customer_id: str | None = None
    plan_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool | None = None
    auto_renew: bool | None = None


class Subscription(BaseDocument):
    """구독 문서."""

    customer_id: str = ""
    plan_id: str = ""
    start_date: date | None = None
    end_date: date | None = None
    is_active: bool = True
    auto_renew: bool = True
