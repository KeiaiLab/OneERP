"""구독 모델 — 고객의 구독 라이프사이클을 관리한다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class SubscriptionCreate(BaseModel):
    """구독 생성 요청 스키마."""

    customer_id: str
    plan_id: str
    start_date: date | None = None
    company: str = ""


class SubscriptionUpdate(BaseModel):
    """구독 수정 요청 스키마."""

    plan_id: str | None = None
    status: str | None = None
    cancel_reason: str | None = None
    end_date: date | None = None


class Subscription(BaseDocument):
    """구독 문서 — 고객 구독 상태를 저장한다."""

    customer_id: str = ""
    plan_id: str = ""
    start_date: date | None = None
    end_date: date | None = None
    current_period_start: date | None = None
    current_period_end: date | None = None
    next_billing_date: date | None = None
    status: str = "draft"  # draft/active/paused/cancelled/expired
    cancel_reason: str = ""
    company: str = ""
