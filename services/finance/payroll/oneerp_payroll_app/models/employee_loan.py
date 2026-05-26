"""직원 대출(EmployeeLoan) 문서 모델.

L2 비즈니스 룰: BR-PAY-017 (직원대출 월상환 급여 공제).
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class EmployeeLoanStatus(StrEnum):
    """직원 대출 상태."""

    DRAFT = "draft"
    APPROVED = "approved"
    DISBURSED = "disbursed"
    REPAID = "repaid"
    DEFAULTED = "defaulted"


class EmployeeLoanCreate(BaseModel):
    """직원 대출 생성 요청 스키마."""

    employee_id: str
    loan_amount: Decimal = Decimal(0)
    interest_rate: Decimal = Decimal(0)
    term_months: int = 0
    monthly_repayment: Decimal = Decimal(0)
    disbursement_date: date | None = None
    outstanding_amount: Decimal = Decimal(0)


class EmployeeLoanUpdate(BaseModel):
    """직원 대출 수정 요청 스키마."""

    employee_id: str | None = None
    loan_amount: Decimal | None = None
    interest_rate: Decimal | None = None
    term_months: int | None = None
    monthly_repayment: Decimal | None = None
    disbursement_date: date | None = None
    outstanding_amount: Decimal | None = None
    status: EmployeeLoanStatus | None = None


class EmployeeLoan(BaseDocument):
    """직원 대출 문서."""

    status: EmployeeLoanStatus = Field(
        default=EmployeeLoanStatus.DRAFT,
        description="직원 대출 상태",
    )
    employee_id: str = ""
    loan_amount: Decimal = Decimal(0)
    interest_rate: Decimal = Decimal(0)
    term_months: int = 0
    monthly_repayment: Decimal = Decimal(0)
    disbursement_date: date | None = None
    outstanding_amount: Decimal = Decimal(0)
