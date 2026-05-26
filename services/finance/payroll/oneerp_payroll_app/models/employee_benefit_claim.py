"""직원 복리후생 청구(EmployeeBenefitClaim) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class EmployeeBenefitClaimStatus(StrEnum):
    """복리후생 청구 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"


class EmployeeBenefitClaimCreate(BaseModel):
    """직원 복리후생 청구 생성 요청 스키마."""

    employee_id: str
    benefit_plan_id: str = ""
    claim_date: date | None = None
    amount: Decimal = Decimal(0)
    description: str = ""
    is_approved: bool = False


class EmployeeBenefitClaimUpdate(BaseModel):
    """직원 복리후생 청구 수정 요청 스키마."""

    employee_id: str | None = None
    benefit_plan_id: str | None = None
    claim_date: date | None = None
    amount: Decimal | None = None
    description: str | None = None
    is_approved: bool | None = None
    status: EmployeeBenefitClaimStatus | None = None


class EmployeeBenefitClaim(BaseDocument):
    """직원 복리후생 청구 문서."""

    status: EmployeeBenefitClaimStatus = Field(
        default=EmployeeBenefitClaimStatus.DRAFT,
        description="복리후생 청구 상태",
    )
    employee_id: str = ""
    benefit_plan_id: str = ""
    claim_date: date | None = None
    amount: Decimal = Decimal(0)
    description: str = ""
    is_approved: bool = False
