"""예약 가능 자원(Resource) 마스터 모델 — 자원 예약 모듈.

회의실, 장비, 차량 등 예약 가능한 자원을 정의한다.

비즈니스 규칙:
- BR-RSV-001: 자원명은 테넌트 내에서 고유해야 한다
- BR-RSV-002: 자원은 활성 예약이 없을 때만 비활성화 가능
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ResourceType(StrEnum):
    """자원 유형."""

    MEETING_ROOM = "meeting_room"
    EQUIPMENT = "equipment"
    VEHICLE = "vehicle"
    FACILITY = "facility"
    OTHER = "other"


class ResourceStatus(StrEnum):
    """자원 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class ResourceCreate(BaseModel):
    """자원 생성 요청 스키마."""

    name: str
    resource_type: ResourceType = ResourceType.MEETING_ROOM
    description: str = ""
    location: str = ""
    capacity: int = Field(default=0, ge=0, description="수용 인원 (회의실 등)")
    status: ResourceStatus = ResourceStatus.ACTIVE
    tags: list[str] = Field(default_factory=list, description="분류 태그")
    available_hours_start: str = Field(default="09:00", description="이용 가능 시작 시간 (HH:MM)")
    available_hours_end: str = Field(default="18:00", description="이용 가능 종료 시간 (HH:MM)")
    manager_id: str = Field(default="", description="자원 관리 담당자 ID")


class ResourceUpdate(BaseModel):
    """자원 수정 요청 스키마."""

    name: str | None = None
    resource_type: ResourceType | None = None
    description: str | None = None
    location: str | None = None
    capacity: int | None = Field(default=None, ge=0)
    status: ResourceStatus | None = None
    tags: list[str] | None = None
    available_hours_start: str | None = None
    available_hours_end: str | None = None
    manager_id: str | None = None


class Resource(BaseDocument):
    """예약 가능 자원 마스터 문서.

    naming prefix: RSC
    """

    name: str = Field(default="", description="자원명")
    resource_type: ResourceType = Field(default=ResourceType.MEETING_ROOM, description="자원 유형")
    description: str = Field(default="", description="설명")
    location: str = Field(default="", description="위치")
    capacity: int = Field(default=0, ge=0, description="수용 인원")
    status: ResourceStatus = Field(default=ResourceStatus.ACTIVE, description="자원 상태")
    tags: list[str] = Field(default_factory=list, description="분류 태그")
    available_hours_start: str = Field(default="09:00", description="이용 가능 시작 시간")
    available_hours_end: str = Field(default="18:00", description="이용 가능 종료 시간")
    manager_id: str = Field(default="", description="관리 담당자 ID")
