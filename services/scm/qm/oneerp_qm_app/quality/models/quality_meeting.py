"""품질 회의(QualityMeeting) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class QualityMeetingCreate(BaseModel):
    """품질 회의 생성 요청 스키마."""

    meeting_title: str
    meeting_date: date | None = None
    attendees: list[str] = Field(default_factory=list)
    agenda: str = ""
    minutes: str = ""


class QualityMeetingUpdate(BaseModel):
    """품질 회의 수정 요청 스키마."""

    meeting_title: str | None = None
    meeting_date: date | None = None
    attendees: list[str] | None = None
    agenda: str | None = None
    minutes: str | None = None


class QualityMeeting(BaseDocument):
    """품질 회의 문서."""

    meeting_title: str = ""
    meeting_date: date | None = None
    attendees: list[str] = Field(default_factory=list)
    agenda: str = ""
    minutes: str = ""
