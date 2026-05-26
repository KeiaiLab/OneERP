"""학습 등록(LearningEnrollment) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class LearningEnrollmentStatus(StrEnum):
    """수강 등록 상태."""

    ENROLLED = "enrolled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class LearningEnrollmentCreate(BaseModel):
    """학습 등록 생성 요청 스키마."""

    employee_id: str
    course_id: str = ""
    enrollment_date: date | None = None
    completion_date: date | None = None
    progress: Decimal = Decimal(0)


class LearningEnrollmentUpdate(BaseModel):
    """학습 등록 수정 요청 스키마."""

    employee_id: str | None = None
    course_id: str | None = None
    enrollment_date: date | None = None
    completion_date: date | None = None
    progress: Decimal | None = None
    status: LearningEnrollmentStatus | None = None


class LearningEnrollment(BaseDocument):
    """학습 등록 문서."""

    status: LearningEnrollmentStatus = Field(
        default=LearningEnrollmentStatus.ENROLLED,
        description="수강 등록 상태",
    )
    employee_id: str = ""
    course_id: str = ""
    enrollment_date: date | None = None
    completion_date: date | None = None
    progress: Decimal = Decimal(0)
