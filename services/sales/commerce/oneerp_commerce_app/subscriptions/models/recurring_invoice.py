"""정기 청구 모델 — 반복적인 청구를 관리한다."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class RecurringInvoiceItem(BaseModel):
    """정기 청구 품목."""

    item_code: str = ""
    item_name: str = ""
    qty: int = 1
    rate: Decimal = Decimal(0)


class RecurringInvoiceCreate(BaseModel):
    """정기 청구 생성 요청 스키마."""

    customer_id: str
    items: list[RecurringInvoiceItem] = []
    frequency: str = "monthly"  # monthly/quarterly/yearly
    next_date: date | None = None
    company: str = ""


class RecurringInvoiceUpdate(BaseModel):
    """정기 청구 수정 요청 스키마."""

    items: list[RecurringInvoiceItem] | None = None
    frequency: str | None = None
    next_date: date | None = None
    status: str | None = None


class RecurringInvoice(BaseDocument):
    """정기 청구 문서 — 반복 청구 정보를 저장한다."""

    customer_id: str = ""
    items: list[RecurringInvoiceItem] = []
    frequency: str = "monthly"  # monthly/quarterly/yearly
    next_date: date | None = None
    template_invoice_id: str = ""
    status: str = "draft"  # draft/active/paused/cancelled
    company: str = ""
