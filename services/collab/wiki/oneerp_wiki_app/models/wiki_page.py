"""위키 페이지(WikiPage) 문서 모델 — 위키 모듈.

위키 페이지는 마크다운 기반 콘텐츠를 저장하는 핵심 엔티티이다.
버전 관리, 발행/보관 워크플로를 지원한다.
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class WikiPageStatus(StrEnum):
    """위키 페이지 상태."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class WikiPageCreate(BaseModel):
    """위키 페이지 생성 요청 스키마."""

    title: str
    content: str = ""
    space_id: str = ""
    parent_page_id: str = ""
    tags: list[str] = []
    author_id: str = ""


class WikiPageUpdate(BaseModel):
    """위키 페이지 수정 요청 스키마."""

    title: str | None = None
    content: str | None = None
    space_id: str | None = None
    parent_page_id: str | None = None
    tags: list[str] | None = None


class WikiPage(BaseDocument):
    """위키 페이지 — 마크다운 기반 지식 문서.

    naming prefix: WP
    """

    title: str = Field(default="", description="페이지 제목")
    content: str = Field(default="", description="마크다운 본문")
    space_id: str = Field(default="", description="소속 위키 공간 ID")
    parent_page_id: str = Field(default="", description="상위 페이지 ID")
    tags: list[str] = Field(default_factory=list, description="태그 목록")
    author_id: str = Field(default="", description="작성자 ID")
    status: WikiPageStatus = Field(
        default=WikiPageStatus.DRAFT,
        description="페이지 상태",
    )
    version: int = Field(default=1, description="현재 버전")
    view_count: int = Field(default=0, description="조회수")
