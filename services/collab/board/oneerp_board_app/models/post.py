"""게시글(Post) 문서 모델.

엔티티 정의: L2-spec 1.2
- BR-BRD-002: 게시글 작성 권한 검증
- BR-BRD-003: 게시글 수정/삭제 권한
- BR-BRD-004: 필독 설정 권한
- BR-BRD-006: 예약 발행 시각 검증
- BR-BRD-009: 익명 게시글 제한
- BR-BRD-016: 카테고리 유효성 검증
- BR-BRD-017: 게시글 상단 고정 제한
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class PostStatus(StrEnum):
    """게시글 상태."""

    DRAFT = "draft"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    ARCHIVED = "archived"
    DELETED = "deleted"


class MustReadTarget(BaseModel):
    """필독 대상 설정 — 임베디드 객체."""

    target_type: str = "all"
    target_ids: list[str] = Field(default_factory=list)
    exclude_ids: list[str] = Field(default_factory=list)


class RevisionEntry(BaseModel):
    """수정 이력 — 임베디드 객체."""

    revision: int
    editor_id: str
    edited_at: datetime
    diff_summary: str | None = None
    previous_title: str | None = None
    previous_content: str | None = None


class TranslationEntry(BaseModel):
    """번역 — 임베디드 객체."""

    title: str
    content: str
    translator_id: str | None = None
    translated_at: datetime


class PostCreate(BaseModel):
    """게시글 생성 요청 스키마."""

    title: str
    content: str
    content_plain: str = ""
    author_id: str = ""
    author_name: str = ""
    is_anonymous: bool = False
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    status: PostStatus = PostStatus.DRAFT
    is_pinned: bool = False
    pin_order: int = 0
    is_notice: bool = False
    is_must_read: bool = False
    must_read_target: MustReadTarget | None = None
    must_read_deadline: datetime | None = None
    scheduled_at: datetime | None = None
    source_type: str | None = None
    source_ref: str | None = None


class PostUpdate(BaseModel):
    """게시글 수정 요청 스키마."""

    title: str | None = None
    content: str | None = None
    content_plain: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    status: PostStatus | None = None
    is_pinned: bool | None = None
    pin_order: int | None = None
    is_notice: bool | None = None
    is_must_read: bool | None = None
    must_read_target: MustReadTarget | None = None
    must_read_deadline: datetime | None = None
    scheduled_at: datetime | None = None


class Post(BaseDocument):
    """게시글 문서.

    BR-BRD-002: 게시글 작성 시 게시판 write 이상 권한 필요.
    BR-BRD-006: 예약 발행 시각은 현재보다 5분 이상 이후.
    BR-BRD-009: 익명 글은 allow_anonymous=true 게시판만 가능.
    BR-BRD-016: category는 게시판 categories 목록에 포함 필수.
    BR-BRD-017: 게시판당 상단 고정 최대 10개.
    """

    board_id: str = ""
    title: str = ""
    content: str = ""
    content_plain: str = ""
    author_id: str = ""
    author_name: str = ""
    is_anonymous: bool = False
    category: str | None = None
    tags: list[str] = Field(default_factory=list)
    status: PostStatus = PostStatus.DRAFT
    is_pinned: bool = False
    pin_order: int = 0
    is_notice: bool = False
    is_must_read: bool = False
    must_read_target: MustReadTarget | None = None
    must_read_deadline: datetime | None = None
    scheduled_at: datetime | None = None
    published_at: datetime | None = None
    view_count: int = 0
    like_count: int = 0
    comment_count: int = 0
    bookmark_count: int = 0
    revision_count: int = 0
    revision_history: list[RevisionEntry] = Field(default_factory=list)
    translations: dict[str, TranslationEntry] = Field(default_factory=dict)
    source_type: str | None = None
    source_ref: str | None = None
    deleted_at: str | None = None
