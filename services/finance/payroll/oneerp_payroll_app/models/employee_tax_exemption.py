"""직원 세금 면제(EmployeeTaxExemption) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class EmployeeTaxExemptionStatus(StrEnum):
    """직원 세금 면제 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    VERIFIED = "verified"


class EmployeeTaxExemptionCreate(BaseModel):
    """직원 세금 면제 생성 요청 스키마."""

    employee_id: str
    fiscal_year: str = ""
    exemption_category: str = ""
    amount: Decimal = Decimal(0)
    proof_submitted: bool = False


class EmployeeTaxExemptionUpdate(BaseModel):
    """직원 세금 면제 수정 요청 스키마."""

    employee_id: str | None = None
    fiscal_year: str | None = None
    exemption_category: str | None = None
    amount: Decimal | None = None
    proof_submitted: bool | None = None
    status: EmployeeTaxExemptionStatus | None = None


class EmployeeTaxExemption(BaseDocument):
    """직원 세금 면제 문서."""

    status: EmployeeTaxExemptionStatus = Field(
        default=EmployeeTaxExemptionStatus.DRAFT,
        description="직원 세금 면제 상태",
    )
    employee_id: str = ""
    fiscal_year: str = ""
    exemption_category: str = ""
    amount: Decimal = Decimal(0)
    proof_submitted: bool = False
