"""학습 과정(LearningCourse) 문서 모델.

L2 비즈니스 룰: BR-HR-016 (학습 과정 필수 여부).
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class LearningCourseStatus(StrEnum):
    """교육 과정 상태."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LearningCourseCreate(BaseModel):
    """학습 과정 생성 요청 스키마."""

    course_name: str
    category: str = ""
    duration_hours: Decimal = Decimal(0)
    is_mandatory: bool = False
    is_active: bool = True


class LearningCourseUpdate(BaseModel):
    """학습 과정 수정 요청 스키마."""

    course_name: str | None = None
    category: str | None = None
    duration_hours: Decimal | None = None
    is_mandatory: bool | None = None
    is_active: bool | None = None
    status: LearningCourseStatus | None = None


class LearningCourse(BaseDocument):
    """학습 과정 문서."""

    status: LearningCourseStatus = Field(
        default=LearningCourseStatus.DRAFT,
        description="교육 과정 상태",
    )
    course_name: str = ""
    category: str = ""
    duration_hours: Decimal = Decimal(0)
    is_mandatory: bool = False
    is_active: bool = True
