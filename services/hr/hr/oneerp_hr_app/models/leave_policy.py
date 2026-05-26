"""휴가 정책(LeavePolicy) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class LeavePolicyStatus(StrEnum):
    """휴가 정책 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class LeavePolicyCreate(BaseModel):
    """휴가 정책 생성 요청 스키마."""

    policy_name: str
    leave_type_id: str = ""
    annual_allocation: Decimal = Decimal(0)
    carry_forward: bool = False
    max_carry_forward_days: Decimal = Decimal(0)


class LeavePolicyUpdate(BaseModel):
    """휴가 정책 수정 요청 스키마."""

    policy_name: str | None = None
    leave_type_id: str | None = None
    annual_allocation: Decimal | None = None
    carry_forward: bool | None = None
    max_carry_forward_days: Decimal | None = None
    status: LeavePolicyStatus | None = None


class LeavePolicy(BaseDocument):
    """휴가 정책 문서."""

    status: LeavePolicyStatus = Field(
        default=LeavePolicyStatus.ACTIVE,
        description="휴가 정책 상태",
    )
    policy_name: str = ""
    leave_type_id: str = ""
    annual_allocation: Decimal = Decimal(0)
    carry_forward: bool = False
    max_carry_forward_days: Decimal = Decimal(0)
