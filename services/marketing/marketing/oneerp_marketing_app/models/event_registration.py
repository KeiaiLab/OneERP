"""행사 등록 모델 — 마케팅 행사의 참석자를 관리한다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class EventAttendee(BaseModel):
    """행사 참석자."""

    contact_id: str = ""
    contact_name: str = ""
    status: str = "registered"  # registered/attended/cancelled
    registered_at: datetime | None = None


class EventRegistrationCreate(BaseModel):
    """행사 등록 생성 요청 스키마."""

    event_name: str
    event_type: str  # seminar/webinar/conference/exhibition
    campaign_id: str = ""
    date: datetime | None = None
    venue: str = ""
    max_attendees: int = 0
    company: str = ""


class EventRegistrationUpdate(BaseModel):
    """행사 등록 수정 요청 스키마."""

    event_name: str | None = None
    event_type: str | None = None
    date: datetime | None = None
    venue: str | None = None
    max_attendees: int | None = None
    status: str | None = None


class EventRegistration(BaseDocument):
    """행사 등록 문서 — 마케팅 행사 정보를 저장한다."""

    event_name: str = ""
    event_type: str = ""  # seminar/webinar/conference/exhibition
    campaign_id: str = ""
    date: datetime | None = None
    venue: str = ""
    max_attendees: int = 0
    registrations: list[EventAttendee] = []
    status: str = "draft"  # draft/confirmed/completed/cancelled
    company: str = ""
