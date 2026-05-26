"""직원 복리후생 플랜(EmployeeBenefitPlan) 문서 모델.

L2 비즈니스 룰: BR-PAY-018 (복리후생 한도 관리).
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class EmployeeBenefitPlanStatus(StrEnum):
    """복리후생 플랜 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class EmployeeBenefitPlanCreate(BaseModel):
    """직원 복리후생 플랜 생성 요청 스키마."""

    plan_name: str
    benefit_type: str = ""
    max_amount: Decimal = Decimal(0)
    is_active: bool = True


class EmployeeBenefitPlanUpdate(BaseModel):
    """직원 복리후생 플랜 수정 요청 스키마."""

    plan_name: str | None = None
    benefit_type: str | None = None
    max_amount: Decimal | None = None
    is_active: bool | None = None
    status: EmployeeBenefitPlanStatus | None = None


class EmployeeBenefitPlan(BaseDocument):
    """직원 복리후생 플랜 문서."""

    status: EmployeeBenefitPlanStatus = Field(
        default=EmployeeBenefitPlanStatus.ACTIVE,
        description="복리후생 플랜 상태",
    )
    plan_name: str = ""
    benefit_type: str = ""
    max_amount: Decimal = Decimal(0)
    is_active: bool = True
