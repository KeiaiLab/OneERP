"""승계 계획(SuccessionPlan) 문서 모델.

L2 비즈니스 룰: BR-HR-019 (승계 계획 후보자 관리).
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class SuccessionPlanStatus(StrEnum):
    """승계 계획 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"


class SuccessionPlanCreate(BaseModel):
    """승계 계획 생성 요청 스키마."""

    position: str
    current_holder_id: str = ""
    successor_ids: list[str] = Field(default_factory=list)
    readiness_level: str = ""


class SuccessionPlanUpdate(BaseModel):
    """승계 계획 수정 요청 스키마."""

    position: str | None = None
    current_holder_id: str | None = None
    successor_ids: list[str] | None = None
    readiness_level: str | None = None
    status: SuccessionPlanStatus | None = None


class SuccessionPlan(BaseDocument):
    """승계 계획 문서."""

    status: SuccessionPlanStatus = Field(
        default=SuccessionPlanStatus.DRAFT,
        description="승계 계획 상태",
    )
    position: str = ""
    current_holder_id: str = ""
    successor_ids: list[str] = Field(default_factory=list)
    readiness_level: str = ""
