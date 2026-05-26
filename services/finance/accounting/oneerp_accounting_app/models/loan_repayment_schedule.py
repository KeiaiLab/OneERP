"""상환 스케줄(LoanRepaymentSchedule) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class LoanRepaymentScheduleCreate(BaseModel):
    """상환 스케줄 생성 요청 스키마."""

    loan_id: str
    installment_no: int = 0
    due_date: date | None = None
    principal: Decimal = Decimal(0)
    interest: Decimal = Decimal(0)
    total_payment: Decimal = Decimal(0)
    is_paid: bool = False


class LoanRepaymentScheduleUpdate(BaseModel):
    """상환 스케줄 수정 요청 스키마."""

    loan_id: str | None = None
    installment_no: int | None = None
    due_date: date | None = None
    principal: Decimal | None = None
    interest: Decimal | None = None
    total_payment: Decimal | None = None
    is_paid: bool | None = None


class LoanRepaymentSchedule(BaseDocument):
    """상환 스케줄 문서."""

    loan_id: str = ""
    installment_no: int = 0
    due_date: date | None = None
    principal: Decimal = Decimal(0)
    interest: Decimal = Decimal(0)
    total_payment: Decimal = Decimal(0)
    is_paid: bool = False
