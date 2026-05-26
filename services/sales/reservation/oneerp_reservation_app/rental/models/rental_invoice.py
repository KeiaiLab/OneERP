"""렌탈 청구서(RentalInvoice) 문서 모델.

렌탈 주문에 기반한 정기 청구서를 관리한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class InvoiceStatus(StrEnum):
    """청구서 상태."""

    DRAFT = "draft"
    ISSUED = "issued"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class RentalInvoiceCreate(BaseModel):
    """렌탈 청구서 생성 요청 스키마."""

    rental_order_id: str
    customer_id: str = ""
    invoice_date: date | None = None
    due_date: date | None = None
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    rental_amount: Decimal = Decimal(0)
    late_fee: Decimal = Decimal(0)
    damage_charge: Decimal = Decimal(0)
    tax_amount: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)
    status: InvoiceStatus = InvoiceStatus.DRAFT
    memo: str = ""


class RentalInvoiceUpdate(BaseModel):
    """렌탈 청구서 수정 요청 스키마."""

    rental_order_id: str | None = None
    customer_id: str | None = None
    invoice_date: date | None = None
    due_date: date | None = None
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    rental_amount: Decimal | None = None
    late_fee: Decimal | None = None
    damage_charge: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None
    status: InvoiceStatus | None = None
    memo: str | None = None


class RentalInvoice(BaseDocument):
    """렌탈 청구서 문서.

    청구 기간, 렌탈 금액, 연체료, 손상 비용, 세금을 포함한다.
    """

    rental_order_id: str = ""
    customer_id: str = ""
    invoice_date: date | None = None
    due_date: date | None = None
    billing_period_start: date | None = None
    billing_period_end: date | None = None
    rental_amount: Decimal = Decimal(0)
    late_fee: Decimal = Decimal(0)
    damage_charge: Decimal = Decimal(0)
    tax_amount: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)
    status: InvoiceStatus = InvoiceStatus.DRAFT
    memo: str = ""
