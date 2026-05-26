"""공지사항 읽음(AnnouncementRead) 문서 모델.

사용자의 공지사항 확인 기록을 관리한다.
BR-PTL-005: '오늘 하루 보지 않기' 기능 지원.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class AnnouncementReadCreate(BaseModel):
    """공지사항 읽음 생성 요청 스키마."""

    announcement_id: str = Field(description="공지사항 ID")
    user_id: str = Field(default="", description="사용자 ID (서버에서 설정)")
    hide_until: datetime | None = Field(
        default=None,
        description="숨김 만료일 (오늘 하루 보지 않기)",
    )


class AnnouncementReadUpdate(BaseModel):
    """공지사항 읽음 수정 요청 스키마."""

    hide_until: datetime | None = None


class AnnouncementRead(BaseDocument):
    """공지사항 읽음 문서.

    BR-PTL-005: hide_until로 '오늘 하루 보지 않기' 구현.
    """

    announcement_id: str = ""
    user_id: str = ""
    read_at: datetime | None = None
    hide_until: datetime | None = None
