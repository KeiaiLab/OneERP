"""위키 댓글(WikiComment) 문서 모델 — 위키 모듈.

위키 페이지에 대한 댓글/토론을 관리한다.
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class WikiCommentCreate(BaseModel):
    """위키 댓글 생성 요청 스키마."""

    page_id: str
    author_id: str = ""
    content: str = ""
    parent_comment_id: str = ""


class WikiCommentUpdate(BaseModel):
    """위키 댓글 수정 요청 스키마."""

    content: str | None = None


class WikiComment(BaseDocument):
    """위키 댓글 — 페이지 토론.

    naming prefix: WC
    """

    page_id: str = Field(default="", description="위키 페이지 ID")
    author_id: str = Field(default="", description="작성자 ID")
    content: str = Field(default="", description="댓글 내용")
    parent_comment_id: str = Field(default="", description="상위 댓글 ID (답글)")
