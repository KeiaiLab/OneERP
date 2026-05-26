"""구독 청구 모델 — 구독 기반 자동 청구를 관리한다."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class BillingPeriod(BaseModel):
    """청구 기간."""

    start: date | None = None
    end: date | None = None


class SubscriptionInvoiceCreate(BaseModel):
    """구독 청구 생성 요청 스키마."""

    subscription_id: str
    billing_period: BillingPeriod | None = None
    amount: Decimal = Decimal(0)
    company: str = ""


class SubscriptionInvoiceUpdate(BaseModel):
    """구독 청구 수정 요청 스키마."""

    status: str | None = None
    sales_invoice_id: str | None = None
    amount: Decimal | None = None


class SubscriptionInvoice(BaseDocument):
    """구독 청구 문서 — 구독 청구 정보를 저장한다."""

    subscription_id: str = ""
    billing_period: BillingPeriod | None = None
    amount: Decimal = Decimal(0)
    sales_invoice_id: str = ""
    status: str = "draft"  # draft/submitted/paid/cancelled
    company: str = ""
