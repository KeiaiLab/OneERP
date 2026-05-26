"""채널(Channel) 문서 모델.

사내 메신저의 대화 채널을 정의한다.
BR-MSG-001: 채널명은 2~100자 이내.
BR-MSG-002: 채널 유형은 public/private/direct 중 하나.
BR-MSG-003: direct 채널은 정확히 2명의 멤버만 허용.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator


class ChannelType(StrEnum):
    """채널 유형."""

    PUBLIC = "public"
    PRIVATE = "private"
    DIRECT = "direct"


class ChannelStatus(StrEnum):
    """채널 상태."""

    ACTIVE = "active"
    ARCHIVED = "archived"


class ChannelCreate(BaseModel):
    """채널 생성 요청 스키마.

    BR-MSG-001: 채널명은 2~100자 이내.
    BR-MSG-002: 채널 유형은 public/private/direct 중 하나.
    """

    channel_name: str = Field(..., min_length=2, max_length=100)
    channel_type: ChannelType = ChannelType.PUBLIC
    description: str = ""
    members: list[str] = Field(default_factory=list)
    owner_id: str = ""

    @field_validator("members")
    @classmethod
    def validate_direct_members(cls, v: list[str], info: object) -> list[str]:
        """BR-MSG-003: direct 채널은 정확히 2명의 멤버만 허용."""
        # info.data에서 channel_type 확인 — Pydantic v2
        data = getattr(info, "data", {})
        if data.get("channel_type") == ChannelType.DIRECT and len(v) != 2:
            msg = "1:1 채널은 정확히 2명의 멤버가 필요합니다"
            raise ValueError(msg)
        return v


class ChannelUpdate(BaseModel):
    """채널 수정 요청 스키마."""

    channel_name: str | None = None
    description: str | None = None
    status: ChannelStatus | None = None


class Channel(BaseDocument):
    """채널 문서.

    BR-MSG-001: 채널명은 2~100자 이내.
    BR-MSG-002: 채널 유형은 public/private/direct 중 하나.
    """

    channel_name: str = ""
    channel_type: ChannelType = ChannelType.PUBLIC
    description: str = ""
    members: list[str] = Field(default_factory=list)
    owner_id: str = ""
    status: ChannelStatus = ChannelStatus.ACTIVE
    pinned_message_ids: list[str] = Field(default_factory=list)
