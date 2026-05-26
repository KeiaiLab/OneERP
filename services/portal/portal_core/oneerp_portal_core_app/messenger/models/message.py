"""메시지(Message) 문서 모델.

사내 메신저의 개별 메시지를 정의한다.
BR-MSG-010: 메시지 본문은 1~10000자 이내.
BR-MSG-011: 메시지 유형은 text/file/system/reply 중 하나.
BR-MSG-012: reply 유형은 parent_message_id가 필수.
BR-MSG-013: 삭제된 메시지는 본문이 "(삭제된 메시지)"로 대체.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator

if TYPE_CHECKING:
    from datetime import datetime


class MessageType(StrEnum):
    """메시지 유형."""

    TEXT = "text"
    FILE = "file"
    SYSTEM = "system"
    REPLY = "reply"


class MessageStatus(StrEnum):
    """메시지 상태."""

    ACTIVE = "active"
    EDITED = "edited"
    DELETED = "deleted"


class Reaction(BaseModel):
    """메시지 리액션."""

    emoji: str = ""
    user_id: str = ""


class MessageCreate(BaseModel):
    """메시지 생성 요청 스키마.

    BR-MSG-010: 메시지 본문은 1~10000자 이내.
    BR-MSG-011: 메시지 유형은 text/file/system/reply 중 하나.
    BR-MSG-012: reply 유형은 parent_message_id가 필수.
    """

    channel_id: str
    sender_id: str
    content: str = Field(..., min_length=1, max_length=10000)
    message_type: MessageType = MessageType.TEXT
    parent_message_id: str | None = None
    file_url: str | None = None
    file_name: str | None = None
    mentions: list[str] = Field(default_factory=list)

    @field_validator("parent_message_id")
    @classmethod
    def validate_reply_parent(cls, v: str | None, info: object) -> str | None:
        """BR-MSG-012: reply 유형은 parent_message_id가 필수."""
        data = getattr(info, "data", {})
        if data.get("message_type") == MessageType.REPLY and not v:
            msg = "답글 메시지는 parent_message_id가 필수입니다"
            raise ValueError(msg)
        return v


class MessageUpdate(BaseModel):
    """메시지 수정 요청 스키마."""

    content: str | None = Field(None, min_length=1, max_length=10000)


class Message(BaseDocument):
    """메시지 문서.

    BR-MSG-010 ~ BR-MSG-013 규칙을 따른다.
    """

    channel_id: str = ""
    sender_id: str = ""
    content: str = ""
    message_type: MessageType = MessageType.TEXT
    status: MessageStatus = MessageStatus.ACTIVE
    parent_message_id: str | None = None
    file_url: str | None = None
    file_name: str | None = None
    mentions: list[str] = Field(default_factory=list)
    reactions: list[Reaction] = Field(default_factory=list)
    edited_at: datetime | None = None
    thread_count: int = 0
