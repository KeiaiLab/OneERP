"""예약(Reservation) 트랜잭션 모델 — 자원 예약 모듈.

자원에 대한 시간 기반 예약을 관리한다.

비즈니스 규칙:
- BR-RSV-003: 동일 자원의 예약 시간은 중복 불가 (시간 충돌 금지)
- BR-RSV-004: 과거 시간에는 예약 생성 불가
- BR-RSV-005: 예약은 시작 시간 이전에만 취소 가능
- BR-RSV-006: 반복 예약 시 각 인스턴스별로 충돌 검증
- BR-RSV-007: 예약 시간은 자원의 이용 가능 시간 내에 있어야 한다

에러 코드:
- ERR-RSV-001: 시간 충돌 (해당 시간에 이미 예약 존재)
- ERR-RSV-002: 과거 시간 예약 시도
- ERR-RSV-003: 자원이 비활성 상태
- ERR-RSV-004: 취소 불가 (이미 시작됨)
- ERR-RSV-005: 자원을 찾을 수 없음
- ERR-RSV-006: 이용 가능 시간 범위 벗어남
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class ReservationStatus(StrEnum):
    """예약 상태."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class RecurrenceType(StrEnum):
    """반복 유형."""

    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class ReservationCreate(BaseModel):
    """예약 생성 요청 스키마."""

    resource_id: str
    title: str = ""
    description: str = ""
    requester_id: str = ""
    requester_name: str = ""
    start_time: datetime
    end_time: datetime
    attendees: list[str] = Field(default_factory=list, description="참석자 ID 목록")
    recurrence_type: RecurrenceType = RecurrenceType.NONE
    recurrence_count: int = Field(default=1, ge=1, le=52, description="반복 횟수")
    notes: str = ""


class ReservationUpdate(BaseModel):
    """예약 수정 요청 스키마."""

    title: str | None = None
    description: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    attendees: list[str] | None = None
    notes: str | None = None


class Reservation(BaseDocument):
    """예약 트랜잭션 문서.

    naming prefix: RSV
    """

    resource_id: str = Field(default="", description="예약 자원 ID")
    title: str = Field(default="", description="예약 제목")
    description: str = Field(default="", description="상세 설명")
    requester_id: str = Field(default="", description="요청자 ID")
    requester_name: str = Field(default="", description="요청자 이름")
    start_time: datetime | None = Field(default=None, description="시작 시간")
    end_time: datetime | None = Field(default=None, description="종료 시간")
    status: ReservationStatus = Field(default=ReservationStatus.DRAFT, description="예약 상태")
    attendees: list[str] = Field(default_factory=list, description="참석자 ID 목록")
    recurrence_type: RecurrenceType = Field(default=RecurrenceType.NONE, description="반복 유형")
    recurrence_count: int = Field(default=1, ge=1, description="반복 횟수")
    parent_reservation_id: str = Field(default="", description="반복 예약의 부모 예약 ID")
    notes: str = Field(default="", description="비고")
    checked_in: bool = Field(default=False, description="체크인 여부")
    checked_in_at: datetime | None = Field(default=None, description="체크인 시각")
