"""사내 메일 메시지(MailMessage) 문서 모델.

BR-MAIL-001: 메시지는 반드시 발신자(sender_id)와 하나 이상의 수신자를 가져야 한다.
BR-MAIL-002: 제목(subject)은 비어있을 수 없다.
BR-MAIL-003: 메시지 전송 후 발신자는 내용을 수정할 수 없다 (submitted 상태).
BR-MAIL-004: 첨부파일 최대 10개, 개당 최대 20MB.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, field_validator


class MailPriority(StrEnum):
    """메일 우선순위."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class MailStatus(StrEnum):
    """메일 상태."""

    DRAFT = "draft"
    SENT = "sent"
    CANCELLED = "cancelled"


class Attachment(BaseModel):
    """첨부파일 정보."""

    file_name: str
    file_url: str
    file_size: int = 0
    mime_type: str = ""


class Recipient(BaseModel):
    """수신자 정보."""

    user_id: str
    recipient_type: str = "to"  # to, cc, bcc


class MailMessageCreate(BaseModel):
    """메일 메시지 생성 요청 스키마.

    BR-MAIL-001: 수신자가 하나 이상 필요하다.
    BR-MAIL-002: 제목은 비어있을 수 없다.
    """

    subject: Annotated[str, Field(min_length=1, max_length=500)]
    body: str = ""
    body_html: str = ""
    sender_id: str = ""
    recipients: list[Recipient] = []
    cc: list[str] = []
    bcc: list[str] = []
    priority: MailPriority = MailPriority.NORMAL
    attachments: list[Attachment] = []
    parent_message_id: str | None = None
    thread_id: str | None = None
    is_reply: bool = False
    is_forward: bool = False
    folder: str = "inbox"
    tags: list[str] = []

    @field_validator("recipients")
    @classmethod
    def _수신자_최소_하나(cls, v: list[Recipient]) -> list[Recipient]:
        """BR-MAIL-001: 수신자가 하나 이상이어야 한다."""
        if not v:
            msg = "수신자가 최소 1명 이상 필요합니다 [ERR-MAIL-001]"
            raise ValueError(msg)
        return v

    @field_validator("attachments")
    @classmethod
    def _첨부파일_제한(cls, v: list[Attachment]) -> list[Attachment]:
        """BR-MAIL-004: 첨부파일은 최대 10개까지 허용한다."""
        max_attachments = 10
        if len(v) > max_attachments:
            msg = f"첨부파일은 최대 {max_attachments}개까지 허용됩니다 [ERR-MAIL-004]"
            raise ValueError(msg)
        max_size = 20 * 1024 * 1024  # 20MB
        for att in v:
            if att.file_size > max_size:
                msg = f"첨부파일 '{att.file_name}'의 크기가 20MB를 초과합니다 [ERR-MAIL-004]"
                raise ValueError(msg)
        return v


class MailMessageUpdate(BaseModel):
    """메일 메시지 수정 요청 스키마.

    BR-MAIL-003: 전송된 메시지는 수정 불가하므로 draft 상태에서만 수정 가능.
    """

    subject: str | None = None
    body: str | None = None
    body_html: str | None = None
    recipients: list[Recipient] | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None
    priority: MailPriority | None = None
    attachments: list[Attachment] | None = None
    folder: str | None = None
    tags: list[str] | None = None


class MailMessage(BaseDocument):
    """사내 메일 메시지 문서.

    BR-MAIL-001 ~ BR-MAIL-004 비즈니스 규칙을 적용한다.
    """

    subject: str = ""
    body: str = ""
    body_html: str = ""
    sender_id: str = ""
    recipients: list[Recipient] = []
    cc: list[str] = []
    bcc: list[str] = []
    priority: MailPriority = MailPriority.NORMAL
    status: MailStatus = MailStatus.DRAFT
    attachments: list[Attachment] = []
    parent_message_id: str | None = None
    thread_id: str | None = None
    is_reply: bool = False
    is_forward: bool = False
    is_read: bool = False
    read_at: str | None = None
    sent_at: str | None = None
    folder: str = "inbox"
    tags: list[str] = []
    is_starred: bool = False
    is_archived: bool = False
    is_deleted: bool = False
