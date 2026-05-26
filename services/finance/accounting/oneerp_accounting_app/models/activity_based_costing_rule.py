"""활동기반원가 규칙(ActivityBasedCostingRule) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ActivityBasedCostingRuleStatus(StrEnum):
    """활동기반원가 규칙 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class ActivityBasedCostingRuleCreate(BaseModel):
    """활동기반원가 규칙 생성 요청 스키마."""

    activity_name: str
    cost_driver: str = ""
    rate_per_unit: Decimal = Decimal(0)
    is_active: bool = True


class ActivityBasedCostingRuleUpdate(BaseModel):
    """활동기반원가 규칙 수정 요청 스키마."""

    activity_name: str | None = None
    cost_driver: str | None = None
    rate_per_unit: Decimal | None = None
    is_active: bool | None = None


class ActivityBasedCostingRule(BaseDocument):
    """활동기반원가 규칙 문서."""

    status: ActivityBasedCostingRuleStatus = Field(
        default=ActivityBasedCostingRuleStatus.ACTIVE,
        description="활동기반원가 규칙 상태",
    )
    activity_name: str = ""
    cost_driver: str = ""
    rate_per_unit: Decimal = Decimal(0)
    is_active: bool = True
