"""반복 청구서(RecurringInvoice) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class RecurringInvoiceCreate(BaseModel):
    """반복 청구서 생성 요청 스키마."""

    customer_id: str
    item_code: str = ""
    amount: Decimal = Decimal(0)
    frequency: str = ""
    next_invoice_date: date | None = None
    is_active: bool = True


class RecurringInvoiceUpdate(BaseModel):
    """반복 청구서 수정 요청 스키마."""

    customer_id: str | None = None
    item_code: str | None = None
    amount: Decimal | None = None
    frequency: str | None = None
    next_invoice_date: date | None = None
    is_active: bool | None = None


class RecurringInvoice(BaseDocument):
    """반복 청구서 문서."""

    customer_id: str = ""
    item_code: str = ""
    amount: Decimal = Decimal(0)
    frequency: str = ""
    next_invoice_date: date | None = None
    is_active: bool = True
