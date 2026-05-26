"""구독 청구서(SubscriptionInvoice) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class SubscriptionInvoiceCreate(BaseModel):
    """구독 청구서 생성 요청 스키마."""

    subscription_id: str
    invoice_date: date | None = None
    amount: Decimal = Decimal(0)
    is_paid: bool = False


class SubscriptionInvoiceUpdate(BaseModel):
    """구독 청구서 수정 요청 스키마."""

    subscription_id: str | None = None
    invoice_date: date | None = None
    amount: Decimal | None = None
    is_paid: bool | None = None


class SubscriptionInvoice(BaseDocument):
    """구독 청구서 문서."""

    subscription_id: str = ""
    invoice_date: date | None = None
    amount: Decimal = Decimal(0)
    is_paid: bool = False
