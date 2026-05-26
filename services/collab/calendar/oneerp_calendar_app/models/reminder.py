"""리마인더(Reminder) 문서 모델.

BR-CAL-030: 리마인더는 이벤트에 소속되어야 한다.
BR-CAL-031: 알림 시간은 이벤트 시작 전이어야 한다.
BR-CAL-032: 알림 방식: email, push, sms 중 선택.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, model_validator


class ReminderMethod(StrEnum):
    """알림 방식."""

    EMAIL = "email"
    PUSH = "push"
    SMS = "sms"


class ReminderCreate(BaseModel):
    """리마인더 생성 요청 스키마."""

    event_id: str
    minutes_before: int = 15
    method: ReminderMethod = ReminderMethod.PUSH

    @model_validator(mode="after")
    def _validate_minutes(self) -> ReminderCreate:
        """BR-CAL-031: 알림 시간은 0 이상이어야 한다."""
        if self.minutes_before < 0:
            msg = "알림 시간은 0 이상이어야 합니다 (ERR-CAL-030)"
            raise ValueError(msg)
        return self


class ReminderUpdate(BaseModel):
    """리마인더 수정 요청 스키마."""

    minutes_before: int | None = None
    method: ReminderMethod | None = None
    is_sent: bool | None = None


class Reminder(BaseDocument):
    """리마인더 문서.

    naming prefix: CREM
    BR-CAL-030: 리마인더는 이벤트에 소속되어야 한다.
    BR-CAL-031: 알림 시간은 이벤트 시작 전이어야 한다.
    """

    event_id: str = Field(default="", description="이벤트 ID")
    minutes_before: int = Field(default=15, description="이벤트 시작 N분 전 알림")
    method: ReminderMethod = Field(default=ReminderMethod.PUSH, description="알림 방식")
    is_sent: bool = Field(default=False, description="발송 완료 여부")
