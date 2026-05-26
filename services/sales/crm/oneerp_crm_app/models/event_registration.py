"""이벤트 등록(EventRegistration) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class EventRegistrationCreate(BaseModel):
    """이벤트 등록 생성 요청 스키마."""

    event_name: str
    participant_name: str = ""
    email: str = ""
    registration_date: date | None = None
    is_attended: bool = False


class EventRegistrationUpdate(BaseModel):
    """이벤트 등록 수정 요청 스키마."""

    event_name: str | None = None
    participant_name: str | None = None
    email: str | None = None
    registration_date: date | None = None
    is_attended: bool | None = None


class EventRegistration(BaseDocument):
    """이벤트 등록 문서."""

    event_name: str = ""
    participant_name: str = ""
    email: str = ""
    registration_date: date | None = None
    is_attended: bool = False
