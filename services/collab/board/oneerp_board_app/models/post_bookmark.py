"""게시글 북마크(PostBookmark) 문서 모델.

엔티티 정의: L2-spec 1.9
- BR-BRD-014: 북마크 중복 방지 (토글)
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class PostBookmarkCreate(BaseModel):
    """북마크 생성 요청 스키마."""

    post_id: str
    user_id: str


class PostBookmarkUpdate(BaseModel):
    """북마크 수정 요청 스키마 (사용하지 않음)."""


class PostBookmark(BaseDocument):
    """게시글 북마크 문서.

    BR-BRD-014: 동일 사용자-게시글 조합은 유니크.
    토글 방식: 존재하면 삭제, 없으면 생성.
    """

    post_id: str = ""
    user_id: str = ""
