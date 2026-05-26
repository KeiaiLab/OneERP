"""수수료 플랜(CommissionPlan) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CommissionPlanCreate(BaseModel):
    """수수료 플랜 생성 요청 스키마."""

    plan_name: str
    commission_type: str = ""
    base_rate: Decimal = Decimal(0)
    is_active: bool = True


class CommissionPlanUpdate(BaseModel):
    """수수료 플랜 수정 요청 스키마."""

    plan_name: str | None = None
    commission_type: str | None = None
    base_rate: Decimal | None = None
    is_active: bool | None = None


class CommissionPlan(BaseDocument):
    """수수료 플랜 문서."""

    plan_name: str = ""
    commission_type: str = ""
    base_rate: Decimal = Decimal(0)
    is_active: bool = True
