"""퇴직금(RetirementPay) 문서 모델 — Payroll 모듈.

L2 비즈니스 룰 매핑:
- BR-PAY-013: 퇴직금 = 1일평균임금 x 30 x (근속일수/365)
"""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class RetirementPayCreate(BaseModel):
    """퇴직금 생성 요청 스키마."""

    employee_id: str
    employment_start: date | None = None
    employment_end: date | None = None
    average_wage: Decimal = Decimal(0)
    service_years: Decimal = Decimal(0)
    retirement_amount: Decimal = Decimal(0)


class RetirementPayUpdate(BaseModel):
    """퇴직금 수정 요청 스키마."""

    employee_id: str | None = None
    employment_start: date | None = None
    employment_end: date | None = None
    average_wage: Decimal | None = None
    service_years: Decimal | None = None
    retirement_amount: Decimal | None = None


class RetirementPay(BaseDocument):
    """퇴직금 문서 — Payroll 퇴직금 트랜잭션.

    naming prefix: RTP
    """

    employee_id: str = Field(default="", alias="employee")
    employment_start: date | None = None
    employment_end: date | None = None
    average_wage: Decimal = Decimal(0)
    service_years: Decimal = Decimal(0)
    retirement_amount: Decimal = Decimal(0)
