"""추가 급여(AdditionalSalary) 문서 모델.

L2 비즈니스 룰: BR-PAY-016 (추가급여 급여반영).
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class AdditionalSalaryStatus(StrEnum):
    """추가 급여 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class AdditionalSalaryCreate(BaseModel):
    """추가 급여 생성 요청 스키마."""

    employee_id: str
    salary_component: str = ""
    amount: Decimal = Decimal(0)
    payroll_date: date | None = None
    reason: str = ""


class AdditionalSalaryUpdate(BaseModel):
    """추가 급여 수정 요청 스키마."""

    employee_id: str | None = None
    salary_component: str | None = None
    amount: Decimal | None = None
    payroll_date: date | None = None
    reason: str | None = None
    status: AdditionalSalaryStatus | None = None


class AdditionalSalary(BaseDocument):
    """추가 급여 문서."""

    status: AdditionalSalaryStatus = Field(
        default=AdditionalSalaryStatus.DRAFT,
        description="추가 급여 상태",
    )
    employee_id: str = ""
    salary_component: str = ""
    amount: Decimal = Decimal(0)
    payroll_date: date | None = None
    reason: str = ""
