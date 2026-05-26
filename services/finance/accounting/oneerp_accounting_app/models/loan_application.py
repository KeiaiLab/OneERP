"""대출 신청(LoanApplication) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class LoanApplicationStatus(StrEnum):
    """대출 신청 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    DISBURSED = "disbursed"
    REPAID = "repaid"


class LoanApplicationCreate(BaseModel):
    """대출 신청 생성 요청 스키마."""

    loan_type: str
    loan_amount: Decimal = Decimal(0)
    interest_rate: Decimal = Decimal(0)
    term_months: int = 0
    start_date: date | None = None
    applicant: str = ""


class LoanApplicationUpdate(BaseModel):
    """대출 신청 수정 요청 스키마."""

    loan_type: str | None = None
    loan_amount: Decimal | None = None
    interest_rate: Decimal | None = None
    term_months: int | None = None
    start_date: date | None = None
    applicant: str | None = None


class LoanApplication(BaseDocument):
    """대출 신청 문서."""

    status: LoanApplicationStatus = Field(
        default=LoanApplicationStatus.DRAFT,
        description="대출 신청 상태",
    )
    loan_type: str = ""
    loan_amount: Decimal = Decimal(0)
    interest_rate: Decimal = Decimal(0)
    term_months: int = 0
    start_date: date | None = None
    applicant: str = ""
