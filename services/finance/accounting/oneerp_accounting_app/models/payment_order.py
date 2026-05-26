"""결제 지시(PaymentOrder) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class PaymentOrderStatus(StrEnum):
    """결제 지시 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    PROCESSED = "processed"
    CANCELLED = "cancelled"


class PaymentOrderCreate(BaseModel):
    """결제 지시 생성 요청 스키마."""

    company: str
    payment_date: date | None = None
    total_amount: Decimal = Decimal(0)
    bank_account_id: str = ""
    memo: str = ""


class PaymentOrderUpdate(BaseModel):
    """결제 지시 수정 요청 스키마."""

    company: str | None = None
    payment_date: date | None = None
    total_amount: Decimal | None = None
    bank_account_id: str | None = None
    memo: str | None = None


class PaymentOrder(BaseDocument):
    """결제 지시 문서."""

    status: PaymentOrderStatus = Field(
        default=PaymentOrderStatus.DRAFT,
        description="결제 지시 상태",
    )
    company: str = ""
    payment_date: date | None = None
    total_amount: Decimal = Decimal(0)
    bank_account_id: str = ""
    memo: str = ""
