"""인재 개발 계획(TalentDevelopmentPlan) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class TalentDevelopmentPlanStatus(StrEnum):
    """인재 개발 계획 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"


class TalentDevelopmentPlanCreate(BaseModel):
    """인재 개발 계획 생성 요청 스키마."""

    employee_id: str
    plan_name: str = ""
    development_areas: list[str] = Field(default_factory=list)
    target_date: date | None = None
    mentor_id: str = ""


class TalentDevelopmentPlanUpdate(BaseModel):
    """인재 개발 계획 수정 요청 스키마."""

    employee_id: str | None = None
    plan_name: str | None = None
    development_areas: list[str] | None = None
    target_date: date | None = None
    mentor_id: str | None = None
    status: TalentDevelopmentPlanStatus | None = None


class TalentDevelopmentPlan(BaseDocument):
    """인재 개발 계획 문서."""

    status: TalentDevelopmentPlanStatus = Field(
        default=TalentDevelopmentPlanStatus.DRAFT,
        description="인재 개발 계획 상태",
    )
    employee_id: str = ""
    plan_name: str = ""
    development_areas: list[str] = Field(default_factory=list)
    target_date: date | None = None
    mentor_id: str = ""
