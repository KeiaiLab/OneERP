"""면접 라운드(InterviewRound) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class InterviewRoundCreate(BaseModel):
    """면접 라운드 생성 요청 스키마."""

    job_applicant_id: str
    round_name: str = ""
    scheduled_date: date | None = None
    interviewers: list[str] = Field(default_factory=list)


class InterviewRoundUpdate(BaseModel):
    """면접 라운드 수정 요청 스키마."""

    job_applicant_id: str | None = None
    round_name: str | None = None
    scheduled_date: date | None = None
    interviewers: list[str] | None = None


class InterviewRound(BaseDocument):
    """면접 라운드 문서."""

    job_applicant_id: str = ""
    round_name: str = ""
    scheduled_date: date | None = None
    interviewers: list[str] = Field(default_factory=list)
