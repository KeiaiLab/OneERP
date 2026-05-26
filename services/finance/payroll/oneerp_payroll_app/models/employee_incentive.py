"""직원 인센티브(EmployeeIncentive) 문서 모델.

L2 비즈니스 룰: BR-PAY-019 (인센티브 세금 적용).
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class EmployeeIncentiveStatus(StrEnum):
    """직원 인센티브 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    CANCELLED = "cancelled"


class EmployeeIncentiveCreate(BaseModel):
    """직원 인센티브 생성 요청 스키마."""

    employee_id: str
    incentive_type: str = ""
    amount: Decimal = Decimal(0)
    payroll_date: date | None = None
    reason: str = ""


class EmployeeIncentiveUpdate(BaseModel):
    """직원 인센티브 수정 요청 스키마."""

    employee_id: str | None = None
    incentive_type: str | None = None
    amount: Decimal | None = None
    payroll_date: date | None = None
    reason: str | None = None
    status: EmployeeIncentiveStatus | None = None


class EmployeeIncentive(BaseDocument):
    """직원 인센티브 문서."""

    status: EmployeeIncentiveStatus = Field(
        default=EmployeeIncentiveStatus.DRAFT,
        description="직원 인센티브 상태",
    )
    employee_id: str = ""
    incentive_type: str = ""
    amount: Decimal = Decimal(0)
    payroll_date: date | None = None
    reason: str = ""
