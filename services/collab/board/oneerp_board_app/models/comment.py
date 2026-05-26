"""댓글(Comment) 문서 모델.

엔티티 정의: L2-spec 1.3
- BR-BRD-008: 댓글 깊이 제한 (최대 3단계)
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class CommentCreate(BaseModel):
    """댓글 생성 요청 스키마."""

    content: str
    parent_id: str | None = None
    is_anonymous: bool = False
    mentions: list[str] = Field(default_factory=list)


class CommentUpdate(BaseModel):
    """댓글 수정 요청 스키마."""

    content: str | None = None


class Comment(BaseDocument):
    """댓글 문서.

    BR-BRD-008: 대댓글 최대 깊이는 3(depth=0~3).
    depth=3인 댓글에는 대댓글 불가.
    """

    post_id: str = ""
    parent_id: str | None = None
    depth: int = 0
    author_id: str = ""
    author_name: str = ""
    is_anonymous: bool = False
    content: str = ""
    mentions: list[str] = Field(default_factory=list)
    like_count: int = 0
    is_deleted: bool = False
    deleted_at: str | None = None
