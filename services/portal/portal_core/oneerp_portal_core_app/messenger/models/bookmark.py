"""북마크(Bookmark) 문서 모델.

사용자가 즐겨찾기한 메시지를 관리한다.
BR-MSG-050: 동일 사용자가 같은 메시지를 중복 북마크할 수 없다.
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class BookmarkCreate(BaseModel):
    """북마크 생성 요청 스키마.

    BR-MSG-050: 동일 메시지 중복 북마크 금지.
    """

    user_id: str
    message_id: str
    channel_id: str
    note: str = ""


class BookmarkUpdate(BaseModel):
    """북마크 수정 요청 스키마."""

    note: str | None = None


class Bookmark(BaseDocument):
    """북마크 문서.

    BR-MSG-050 규칙을 따른다.
    """

    user_id: str = ""
    message_id: str = ""
    channel_id: str = ""
    note: str = ""
