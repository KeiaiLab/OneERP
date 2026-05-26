"""목표 설정(GoalSetting) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class GoalSettingStatus(StrEnum):
    """목표 설정 상태."""

    DRAFT = "draft"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class GoalSettingCreate(BaseModel):
    """목표 설정 생성 요청 스키마."""

    employee_id: str
    goal_name: str = ""
    description: str = ""
    target_date: date | None = None
    progress: Decimal = Decimal(0)
    is_completed: bool = False


class GoalSettingUpdate(BaseModel):
    """목표 설정 수정 요청 스키마."""

    employee_id: str | None = None
    goal_name: str | None = None
    description: str | None = None
    target_date: date | None = None
    progress: Decimal | None = None
    is_completed: bool | None = None
    status: GoalSettingStatus | None = None


class GoalSetting(BaseDocument):
    """목표 설정 문서."""

    status: GoalSettingStatus = Field(
        default=GoalSettingStatus.DRAFT,
        description="목표 설정 상태",
    )
    employee_id: str = ""
    goal_name: str = ""
    description: str = ""
    target_date: date | None = None
    progress: Decimal = Decimal(0)
    is_completed: bool = False
