"""초과근무 정책(OvertimePolicy) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class OvertimePolicyStatus(StrEnum):
    """초과근무 정책 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class OvertimePolicyCreate(BaseModel):
    """초과근무 정책 생성 요청 스키마."""

    policy_name: str
    hourly_rate_multiplier: Decimal = Decimal("1.5")
    max_hours_per_month: Decimal = Decimal(52)
    is_active: bool = True


class OvertimePolicyUpdate(BaseModel):
    """초과근무 정책 수정 요청 스키마."""

    policy_name: str | None = None
    hourly_rate_multiplier: Decimal | None = None
    max_hours_per_month: Decimal | None = None
    is_active: bool | None = None
    status: OvertimePolicyStatus | None = None


class OvertimePolicy(BaseDocument):
    """초과근무 정책 문서."""

    status: OvertimePolicyStatus = Field(
        default=OvertimePolicyStatus.ACTIVE,
        description="초과근무 정책 상태",
    )
    policy_name: str = ""
    hourly_rate_multiplier: Decimal = Decimal("1.5")
    max_hours_per_month: Decimal = Decimal(52)
    is_active: bool = True
