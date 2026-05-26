"""예약 정책(ReservationPolicy) 마스터 모델 — 자원 예약 모듈.

자원 유형별 예약 규칙 (최대 시간, 사전 예약 가능 일수, 취소 정책 등)을 정의한다.

비즈니스 규칙:
- BR-RSV-008: 정책에 정의된 최대 예약 시간을 초과 불가
- BR-RSV-009: 사전 예약 가능 일수 이전의 예약 생성 불가
- BR-RSV-010: 취소 마감 시간 이후에는 취소 불가
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

from .resource import ResourceType


class ReservationPolicyCreate(BaseModel):
    """예약 정책 생성 요청 스키마."""

    name: str
    resource_type: ResourceType = ResourceType.MEETING_ROOM
    max_duration_minutes: int = Field(default=120, ge=15, description="최대 예약 시간 (분)")
    max_advance_days: int = Field(default=30, ge=1, description="사전 예약 가능 일수")
    cancellation_deadline_minutes: int = Field(
        default=30, ge=0, description="취소 마감 시간 (시작 전 분)"
    )
    max_concurrent_reservations: int = Field(
        default=3, ge=1, description="사용자당 최대 동시 예약 수"
    )
    auto_release_minutes: int = Field(default=15, ge=0, description="미체크인 자동 해제 시간 (분)")
    requires_approval: bool = Field(default=False, description="승인 필요 여부")
    description: str = ""


class ReservationPolicyUpdate(BaseModel):
    """예약 정책 수정 요청 스키마."""

    name: str | None = None
    resource_type: ResourceType | None = None
    max_duration_minutes: int | None = Field(default=None, ge=15)
    max_advance_days: int | None = Field(default=None, ge=1)
    cancellation_deadline_minutes: int | None = Field(default=None, ge=0)
    max_concurrent_reservations: int | None = Field(default=None, ge=1)
    auto_release_minutes: int | None = Field(default=None, ge=0)
    requires_approval: bool | None = None
    description: str | None = None


class ReservationPolicy(BaseDocument):
    """예약 정책 마스터 문서.

    naming prefix: RPL
    """

    name: str = Field(default="", description="정책명")
    resource_type: ResourceType = Field(
        default=ResourceType.MEETING_ROOM, description="대상 자원 유형"
    )
    max_duration_minutes: int = Field(default=120, ge=15, description="최대 예약 시간 (분)")
    max_advance_days: int = Field(default=30, ge=1, description="사전 예약 가능 일수")
    cancellation_deadline_minutes: int = Field(
        default=30, ge=0, description="취소 마감 시간 (시작 전 분)"
    )
    max_concurrent_reservations: int = Field(
        default=3, ge=1, description="사용자당 최대 동시 예약 수"
    )
    auto_release_minutes: int = Field(default=15, ge=0, description="미체크인 자동 해제 시간 (분)")
    requires_approval: bool = Field(default=False, description="승인 필요 여부")
    description: str = Field(default="", description="정책 설명")
