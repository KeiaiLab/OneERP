"""결제 입력(PaymentEntry) 트랜잭션 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument, LineItem
from pydantic import BaseModel


class PaymentEntryItem(LineItem):
    """결제 입력 라인 아이템 — 참조 문서별 할당 금액."""

    reference_type: str = ""
    reference_id: str = ""
    total_amount: Decimal = Decimal(0)
    outstanding_amount: Decimal = Decimal(0)
    allocated_amount: Decimal = Decimal(0)


class PaymentEntryCreate(BaseModel):
    """결제 입력 생성 요청 스키마."""

    payment_type: str = "receive"
    party_type: str = "customer"
    party: str = ""
    party_id: str = ""
    party_name: str = ""
    posting_date: date | None = None
    paid_amount: Decimal = Decimal(0)
    received_amount: Decimal = Decimal(0)
    reference_no: str = ""
    reference_doctype: str = ""
    reference_name: str = ""
    reference_date: date | None = None
    payment_method: str = ""
    items: list[PaymentEntryItem] = []


class PaymentEntryUpdate(BaseModel):
    """결제 입력 수정 요청 스키마."""

    payment_type: str | None = None
    party_type: str | None = None
    party: str | None = None
    party_id: str | None = None
    party_name: str | None = None
    posting_date: date | None = None
    paid_amount: Decimal | None = None
    received_amount: Decimal | None = None
    reference_no: str | None = None
    reference_doctype: str | None = None
    reference_name: str | None = None
    reference_date: date | None = None
    payment_method: str | None = None
    items: list[PaymentEntryItem] | None = None


class PaymentEntry(BaseDocument):
    """결제 입력 트랜잭션 — 수금/지급 처리.

    naming prefix: PE
    """

    payment_type: str = "receive"
    party_type: str = "customer"
    party: str = ""
    party_id: str = ""
    party_name: str = ""
    posting_date: date | None = None
    paid_amount: Decimal = Decimal(0)
    received_amount: Decimal = Decimal(0)
    reference_no: str = ""
    reference_doctype: str = ""
    reference_name: str = ""
    reference_date: date | None = None
    payment_method: str = ""
    items: list[PaymentEntryItem] = []


_PAYMENT_ENTRY_TYPES = {"date": __import__("datetime").date}

PaymentEntryCreate.model_rebuild(_types_namespace=_PAYMENT_ENTRY_TYPES)
PaymentEntryUpdate.model_rebuild(_types_namespace=_PAYMENT_ENTRY_TYPES)
PaymentEntry.model_rebuild(_types_namespace=_PAYMENT_ENTRY_TYPES)
