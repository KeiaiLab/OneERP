"""게시글 좋아요(PostLike) 문서 모델.

엔티티 정의: L2-spec 1.8
- BR-BRD-014: 좋아요 중복 방지 (토글)
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class PostLikeCreate(BaseModel):
    """좋아요 생성 요청 스키마."""

    post_id: str
    user_id: str


class PostLikeUpdate(BaseModel):
    """좋아요 수정 요청 스키마 (사용하지 않음)."""


class PostLike(BaseDocument):
    """게시글 좋아요 문서.

    BR-BRD-014: 동일 사용자-게시글 조합은 유니크.
    토글 방식: 존재하면 삭제, 없으면 생성.
    """

    post_id: str = ""
    user_id: str = ""
