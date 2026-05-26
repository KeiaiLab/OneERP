"""인사 평가(Appraisal) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class AppraisalStatus(StrEnum):
    """인사고과 상태."""

    DRAFT = "draft"
    SELF_REVIEW = "self_review"
    MANAGER_REVIEW = "manager_review"
    CALIBRATED = "calibrated"
    COMPLETED = "completed"


class AppraisalCreate(BaseModel):
    """인사 평가 생성 요청 스키마."""

    employee_id: str
    appraisal_cycle_id: str = ""
    reviewer_id: str = ""
    score: Decimal = Decimal(0)
    grade: str = ""
    comments: str = ""


class AppraisalUpdate(BaseModel):
    """인사 평가 수정 요청 스키마."""

    employee_id: str | None = None
    appraisal_cycle_id: str | None = None
    reviewer_id: str | None = None
    score: Decimal | None = None
    grade: str | None = None
    comments: str | None = None
    status: AppraisalStatus | None = None


class Appraisal(BaseDocument):
    """인사 평가 문서."""

    status: AppraisalStatus = Field(
        default=AppraisalStatus.DRAFT,
        description="인사고과 상태",
    )
    employee_id: str = ""
    appraisal_cycle_id: str = ""
    reviewer_id: str = ""
    score: Decimal = Decimal(0)
    grade: str = ""
    comments: str = ""
