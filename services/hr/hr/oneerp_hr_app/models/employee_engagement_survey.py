"""직원 참여도 설문(EmployeeEngagementSurvey) 문서 모델.

L2 비즈니스 룰: BR-HR-020 (참여도 조사 관리).
"""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class EmployeeEngagementSurveyStatus(StrEnum):
    """직원 참여도 설문 상태."""

    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"


class EmployeeEngagementSurveyCreate(BaseModel):
    """직원 참여도 설문 생성 요청 스키마."""

    survey_name: str
    start_date: date | None = None
    end_date: date | None = None
    response_count: int = 0
    average_score: Decimal = Decimal(0)


class EmployeeEngagementSurveyUpdate(BaseModel):
    """직원 참여도 설문 수정 요청 스키마."""

    survey_name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    response_count: int | None = None
    average_score: Decimal | None = None
    status: EmployeeEngagementSurveyStatus | None = None


class EmployeeEngagementSurvey(BaseDocument):
    """직원 참여도 설문 문서."""

    status: EmployeeEngagementSurveyStatus = Field(
        default=EmployeeEngagementSurveyStatus.DRAFT,
        description="직원 참여도 설문 상태",
    )
    survey_name: str = ""
    start_date: date | None = None
    end_date: date | None = None
    response_count: int = 0
    average_score: Decimal = Decimal(0)
