"""캘린더 이벤트(CalendarEvent) 문서 모델.

BR-CAL-010: 이벤트는 반드시 캘린더에 속해야 한다.
BR-CAL-011: 종료 시각은 시작 시각 이후여야 한다.
BR-CAL-012: 종일 이벤트는 시간 없이 날짜만 사용한다.
BR-CAL-013: 반복 이벤트는 recurrence_rule이 필수이다.
BR-CAL-014: 이벤트 상태 전이: draft → confirmed → cancelled.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from datetime import datetime


class EventStatus(StrEnum):
    """이벤트 상태."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class EventType(StrEnum):
    """이벤트 유형."""

    MEETING = "meeting"
    TASK = "task"
    REMINDER = "reminder"
    OUT_OF_OFFICE = "out_of_office"
    HOLIDAY = "holiday"
    CUSTOM = "custom"


class RecurrenceFrequency(StrEnum):
    """반복 주기."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class CalendarEventCreate(BaseModel):
    """캘린더 이벤트 생성 요청 스키마."""

    calendar_id: str
    title: str
    description: str = ""
    event_type: EventType = EventType.MEETING
    start_dt: datetime
    end_dt: datetime
    all_day: bool = False
    location: str = ""
    organizer_id: str = ""
    recurrence_frequency: RecurrenceFrequency | None = None
    recurrence_interval: int = 1
    recurrence_end_date: datetime | None = None
    recurrence_count: int | None = None
    ref_doctype: str = ""
    ref_docname: str = ""

    @model_validator(mode="after")
    def _validate_dates(self) -> CalendarEventCreate:
        """BR-CAL-011: 종료 시각은 시작 시각 이후여야 한다."""
        if not self.all_day and self.end_dt <= self.start_dt:
            msg = "종료 시각은 시작 시각 이후여야 합니다 (ERR-CAL-010)"
            raise ValueError(msg)
        return self


class CalendarEventUpdate(BaseModel):
    """캘린더 이벤트 수정 요청 스키마."""

    title: str | None = None
    description: str | None = None
    event_type: EventType | None = None
    start_dt: datetime | None = None
    end_dt: datetime | None = None
    all_day: bool | None = None
    location: str | None = None
    status: EventStatus | None = None
    recurrence_frequency: RecurrenceFrequency | None = None
    recurrence_interval: int | None = None
    recurrence_end_date: datetime | None = None
    recurrence_count: int | None = None


class CalendarEvent(BaseDocument):
    """캘린더 이벤트 문서.

    naming prefix: CEVT
    BR-CAL-010: 이벤트는 반드시 캘린더에 속해야 한다.
    BR-CAL-011: 종료 시각은 시작 시각 이후여야 한다.
    BR-CAL-014: 이벤트 상태 전이: draft → confirmed → cancelled.
    """

    calendar_id: str = Field(default="", description="소속 캘린더 ID")
    title: str = Field(default="", description="이벤트 제목")
    description: str = Field(default="", description="설명")
    event_type: EventType = Field(default=EventType.MEETING, description="이벤트 유형")
    start_dt: datetime | None = Field(default=None, description="시작 일시")
    end_dt: datetime | None = Field(default=None, description="종료 일시")
    all_day: bool = Field(default=False, description="종일 이벤트 여부")
    location: str = Field(default="", description="장소")
    organizer_id: str = Field(default="", description="주최자 ID")
    status: EventStatus = Field(default=EventStatus.DRAFT, description="이벤트 상태")
    recurrence_frequency: RecurrenceFrequency | None = Field(
        default=None,
        description="반복 주기",
    )
    recurrence_interval: int = Field(default=1, description="반복 간격")
    recurrence_end_date: datetime | None = Field(default=None, description="반복 종료일")
    recurrence_count: int | None = Field(default=None, description="반복 횟수")
    ref_doctype: str = Field(default="", description="참조 문서 유형")
    ref_docname: str = Field(default="", description="참조 문서 ID")
