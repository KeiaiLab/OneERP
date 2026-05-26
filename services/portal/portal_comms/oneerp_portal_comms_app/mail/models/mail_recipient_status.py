"""수신자별 메일 상태(MailRecipientStatus) 문서 모델.

BR-MAIL-030: 수신자별로 읽음/안읽음 상태를 독립적으로 관리한다.
BR-MAIL-031: 수신자가 삭제해도 발신자의 메시지는 유지된다.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class RecipientMailStatus(StrEnum):
    """수신자별 메일 상태."""

    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MailRecipientStatusCreate(BaseModel):
    """수신자별 메일 상태 생성 요청 스키마."""

    message_id: str
    user_id: str
    status: RecipientMailStatus = RecipientMailStatus.UNREAD
    folder: str = "inbox"
    is_starred: bool = False


class MailRecipientStatusUpdate(BaseModel):
    """수신자별 메일 상태 수정 요청 스키마."""

    status: RecipientMailStatus | None = None
    folder: str | None = None
    is_starred: bool | None = None


class MailRecipientStatus(BaseDocument):
    """수신자별 메일 상태 문서.

    BR-MAIL-030 ~ BR-MAIL-031 비즈니스 규칙을 적용한다.
    """

    message_id: str = ""
    user_id: str = ""
    status: RecipientMailStatus = RecipientMailStatus.UNREAD
    folder: str = "inbox"
    is_starred: bool = False
    is_deleted: bool = False
    read_at: str | None = None
    deleted_at: str | None = None
