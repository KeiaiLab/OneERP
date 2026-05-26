"""리스 상환 스케줄(LeasePaymentSchedule) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class LeasePaymentScheduleCreate(BaseModel):
    """리스 상환 스케줄 생성 요청 스키마."""

    lease_id: str
    payment_no: int = 0
    due_date: date | None = None
    payment_amount: Decimal = Decimal(0)
    principal: Decimal = Decimal(0)
    interest: Decimal = Decimal(0)
    is_paid: bool = False


class LeasePaymentScheduleUpdate(BaseModel):
    """리스 상환 스케줄 수정 요청 스키마."""

    lease_id: str | None = None
    payment_no: int | None = None
    due_date: date | None = None
    payment_amount: Decimal | None = None
    principal: Decimal | None = None
    interest: Decimal | None = None
    is_paid: bool | None = None


class LeasePaymentSchedule(BaseDocument):
    """리스 상환 스케줄 문서."""

    lease_id: str = ""
    payment_no: int = 0
    due_date: date | None = None
    payment_amount: Decimal = Decimal(0)
    principal: Decimal = Decimal(0)
    interest: Decimal = Decimal(0)
    is_paid: bool = False
