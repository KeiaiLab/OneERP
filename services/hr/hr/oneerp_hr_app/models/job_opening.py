"""채용 공고(JobOpening) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class JobOpeningStatus(StrEnum):
    """채용 공고 상태."""

    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"


class JobOpeningCreate(BaseModel):
    """채용 공고 생성 요청 스키마."""

    title: str
    department_id: str = ""
    designation: str = ""
    vacancies: int = 1
    description: str = ""


class JobOpeningUpdate(BaseModel):
    """채용 공고 수정 요청 스키마."""

    title: str | None = None
    department_id: str | None = None
    designation: str | None = None
    vacancies: int | None = None
    description: str | None = None
    status: JobOpeningStatus | None = None


class JobOpening(BaseDocument):
    """채용 공고 문서."""

    status: JobOpeningStatus = Field(
        default=JobOpeningStatus.DRAFT,
        description="채용 공고 상태",
    )
    title: str = ""
    department_id: str = ""
    designation: str = ""
    vacancies: int = 1
    description: str = ""
