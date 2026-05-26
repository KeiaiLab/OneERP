"""자원(Resource) 문서 모델 — 회의실, 장비 등 예약 가능 자원.

BR-CAL-040: 자원은 고유한 이름을 가져야 한다.
BR-CAL-041: 자원은 최대 수용량을 설정할 수 있다.
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
    OTHER = "other"


class ResourceStatus(StrEnum):
    """자원 상태."""

    AVAILABLE = "available"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class ResourceCreate(BaseModel):
    """자원 생성 요청 스키마."""

    name: str
    resource_type: ResourceType = ResourceType.MEETING_ROOM
    description: str = ""
    capacity: int = 0
    location: str = ""


class ResourceUpdate(BaseModel):
    """자원 수정 요청 스키마."""

    name: str | None = None
    resource_type: ResourceType | None = None
    description: str | None = None
    capacity: int | None = None
    location: str | None = None
    status: ResourceStatus | None = None


class Resource(BaseDocument):
    """예약 가능 자원 문서.

    naming prefix: CRES
    BR-CAL-040: 자원은 고유한 이름을 가져야 한다.
    """

    name: str = Field(default="", description="자원 이름")
    resource_type: ResourceType = Field(
        default=ResourceType.MEETING_ROOM,
        description="자원 유형",
    )
    description: str = Field(default="", description="설명")
    capacity: int = Field(default=0, description="최대 수용량")
    location: str = Field(default="", description="위치")
    status: ResourceStatus = Field(default=ResourceStatus.AVAILABLE, description="상태")
