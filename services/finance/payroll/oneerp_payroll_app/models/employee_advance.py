"""직원 선지급(EmployeeAdvance) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class EmployeeAdvanceStatus(StrEnum):
    """직원 선급금 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    PAID = "paid"
    RETURNED = "returned"
    CANCELLED = "cancelled"


class EmployeeAdvanceCreate(BaseModel):
    """직원 선지급 생성 요청 스키마."""

    employee_id: str
    advance_date: date | None = None
    amount: Decimal = Decimal(0)
    purpose: str = ""
    is_repaid: bool = False
    repaid_amount: Decimal = Decimal(0)


class EmployeeAdvanceUpdate(BaseModel):
    """직원 선지급 수정 요청 스키마."""

    employee_id: str | None = None
    advance_date: date | None = None
    amount: Decimal | None = None
    purpose: str | None = None
    is_repaid: bool | None = None
    repaid_amount: Decimal | None = None
    status: EmployeeAdvanceStatus | None = None


class EmployeeAdvance(BaseDocument):
    """직원 선지급 문서."""

    status: EmployeeAdvanceStatus = Field(
        default=EmployeeAdvanceStatus.DRAFT,
        description="직원 선급금 상태",
    )
    employee_id: str = ""
    advance_date: date | None = None
    amount: Decimal = Decimal(0)
    purpose: str = ""
    is_repaid: bool = False
    repaid_amount: Decimal = Decimal(0)
