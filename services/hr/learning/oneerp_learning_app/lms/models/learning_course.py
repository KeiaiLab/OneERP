"""교육 과정(LearningCourse) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class LearningCourseCreate(BaseModel):
    """교육 과정 생성 요청 스키마."""

    course_name: str
    course_code: str
    course_type: str = "online"
    category: str = ""
    description: str = ""
    duration_hours: Decimal = Decimal(0)
    max_enrollment: int = 0
    is_mandatory: bool = False
    mandatory_frequency: str = ""
    instructor: str = ""
    status: str = "draft"


class LearningCourseUpdate(BaseModel):
    """교육 과정 수정 요청 스키마."""

    course_name: str | None = None
    course_code: str | None = None
    course_type: str | None = None
    category: str | None = None
    description: str | None = None
    duration_hours: Decimal | None = None
    max_enrollment: int | None = None
    is_mandatory: bool | None = None
    mandatory_frequency: str | None = None
    instructor: str | None = None
    status: str | None = None


class LearningCourse(BaseDocument):
    """교육 과정 문서."""

    course_name: str = ""
    course_code: str = ""
    course_type: str = "online"
    category: str = ""
    description: str = ""
    duration_hours: Decimal = Decimal(0)
    max_enrollment: int = 0
    is_mandatory: bool = False
    mandatory_frequency: str = ""
    instructor: str = ""
    status: str = "draft"
