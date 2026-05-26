"""필독 확인(ReadConfirmation) 문서 모델.

엔티티 정의: L2-spec 1.5
- BR-BRD-010: 필독 확인 생성 자동화
- BR-BRD-011: 필독 리마인더 자동 발송
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class ReadStatus(StrEnum):
    """필독 확인 상태."""

    UNREAD = "unread"
    READ = "read"
    REMINDED = "reminded"


class ReadConfirmationCreate(BaseModel):
    """필독 확인 생성 요청 스키마."""

    post_id: str
    user_id: str
    status: ReadStatus = ReadStatus.UNREAD


class ReadConfirmationUpdate(BaseModel):
    """필독 확인 수정 요청 스키마."""

    status: ReadStatus | None = None
    read_at: datetime | None = None
    reminder_count: int | None = None
    last_reminded_at: datetime | None = None


class ReadConfirmation(BaseDocument):
    """필독 확인 문서.

    BR-BRD-010: 게시글 publish 시 is_must_read=true이면
    대상자별 ReadConfirmation(status=unread) 자동 생성.
    BR-BRD-011: 마감일 3일/1일 전 미확인자에게 리마인더 자동 발송.
    """

    post_id: str = ""
    user_id: str = ""
    status: ReadStatus = ReadStatus.UNREAD
    read_at: datetime | None = None
    reminder_count: int = 0
    last_reminded_at: datetime | None = None
