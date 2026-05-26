"""수강 등록(LearningEnrollment) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class LearningEnrollmentCreate(BaseModel):
    """수강 등록 생성 요청 스키마."""

    employee_id: str
    course_id: str
    enrollment_date: date | None = None
    start_date: date | None = None
    completion_date: date | None = None
    progress_pct: Decimal = Decimal(0)
    score: Decimal = Decimal(0)
    status: str = "enrolled"


class LearningEnrollmentUpdate(BaseModel):
    """수강 등록 수정 요청 스키마."""

    employee_id: str | None = None
    course_id: str | None = None
    enrollment_date: date | None = None
    start_date: date | None = None
    completion_date: date | None = None
    progress_pct: Decimal | None = None
    score: Decimal | None = None
    status: str | None = None


class LearningEnrollment(BaseDocument):
    """수강 등록 문서."""

    employee_id: str = ""
    course_id: str = ""
    enrollment_date: date | None = None
    start_date: date | None = None
    completion_date: date | None = None
    progress_pct: Decimal = Decimal(0)
    score: Decimal = Decimal(0)
    status: str = "enrolled"
