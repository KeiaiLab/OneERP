"""입사 지원자(JobApplicant) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class JobApplicantStatus(StrEnum):
    """지원자 상태."""

    APPLIED = "applied"
    SHORTLISTED = "shortlisted"
    INTERVIEWED = "interviewed"
    SELECTED = "selected"
    REJECTED = "rejected"


class JobApplicantCreate(BaseModel):
    """입사 지원자 생성 요청 스키마."""

    applicant_name: str
    email: str = ""
    phone: str = ""
    job_opening_id: str = ""
    resume_link: str = ""
    stage: str = ""


class JobApplicantUpdate(BaseModel):
    """입사 지원자 수정 요청 스키마."""

    applicant_name: str | None = None
    email: str | None = None
    phone: str | None = None
    job_opening_id: str | None = None
    resume_link: str | None = None
    stage: str | None = None
    status: JobApplicantStatus | None = None


class JobApplicant(BaseDocument):
    """입사 지원자 문서."""

    status: JobApplicantStatus = Field(
        default=JobApplicantStatus.APPLIED,
        description="지원자 상태",
    )
    applicant_name: str = ""
    email: str = ""
    phone: str = ""
    job_opening_id: str = ""
    resume_link: str = ""
    stage: str = ""
