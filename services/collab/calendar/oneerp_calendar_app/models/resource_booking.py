"""자원 예약(ResourceBooking) 문서 모델.

BR-CAL-050: 자원 예약은 이벤트 및 자원에 연결되어야 한다.
BR-CAL-051: 동일 자원의 시간 중복 예약 불가.
BR-CAL-052: 예약 종료 시각은 시작 시각 이후여야 한다.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from datetime import datetime


class BookingStatus(StrEnum):
    """예약 상태."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


class ResourceBookingCreate(BaseModel):
    """자원 예약 생성 요청 스키마."""

    event_id: str
    resource_id: str
    start_dt: datetime
    end_dt: datetime
    booked_by: str = ""

    @model_validator(mode="after")
    def _validate_booking_dates(self) -> ResourceBookingCreate:
        """BR-CAL-052: 예약 종료 시각은 시작 시각 이후여야 한다."""
        if self.end_dt <= self.start_dt:
            msg = "예약 종료 시각은 시작 시각 이후여야 합니다 (ERR-CAL-050)"
            raise ValueError(msg)
        return self


class ResourceBookingUpdate(BaseModel):
    """자원 예약 수정 요청 스키마."""

    start_dt: datetime | None = None
    end_dt: datetime | None = None
    status: BookingStatus | None = None


class ResourceBooking(BaseDocument):
    """자원 예약 문서.

    naming prefix: CRBK
    BR-CAL-050: 자원 예약은 이벤트 및 자원에 연결되어야 한다.
    BR-CAL-051: 동일 자원의 시간 중복 예약 불가.
    """

    event_id: str = Field(default="", description="이벤트 ID")
    resource_id: str = Field(default="", description="자원 ID")
    start_dt: datetime | None = Field(default=None, description="예약 시작 일시")
    end_dt: datetime | None = Field(default=None, description="예약 종료 일시")
    booked_by: str = Field(default="", description="예약자 ID")
    status: BookingStatus = Field(default=BookingStatus.PENDING, description="예약 상태")
