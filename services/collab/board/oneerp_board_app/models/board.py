"""게시판(Board) 문서 모델.

엔티티 정의: L2-spec 1.1
- BR-BRD-001: 게시판명 테넌트 내 유니크
- BR-BRD-013: 게시글이 존재하는 게시판 삭제 불가
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class BoardType(StrEnum):
    """게시판 유형."""

    NOTICE = "notice"
    GENERAL = "general"
    QNA = "qna"
    SUGGESTION = "suggestion"
    GALLERY = "gallery"
    ANONYMOUS = "anonymous"


class BoardScope(StrEnum):
    """게시판 범위."""

    COMPANY = "company"
    DEPARTMENT = "department"
    GROUP = "group"
    PROJECT = "project"


class NotificationConfig(BaseModel):
    """알림 설정 — 임베디드 객체."""

    notify_on_new_post: bool = True
    notify_on_comment: bool = True
    notify_channels: list[str] = Field(default_factory=lambda: ["in_app"])


class BoardCreate(BaseModel):
    """게시판 생성 요청 스키마."""

    board_name: str
    board_type: BoardType = BoardType.GENERAL
    scope: BoardScope = BoardScope.COMPANY
    scope_id: str | None = None
    description: str = ""
    categories: list[str] = Field(default_factory=list)
    is_active: bool = True
    allow_anonymous: bool = False
    allow_comments: bool = True
    allow_attachments: bool = True
    max_attachment_size_mb: int = 50
    max_attachments_per_post: int = 10
    sort_order: int = 0
    template_id: str | None = None
    auto_archive_days: int | None = None
    notification_settings: NotificationConfig | None = None


class BoardUpdate(BaseModel):
    """게시판 수정 요청 스키마."""

    board_name: str | None = None
    board_type: BoardType | None = None
    scope: BoardScope | None = None
    scope_id: str | None = None
    description: str | None = None
    categories: list[str] | None = None
    is_active: bool | None = None
    allow_anonymous: bool | None = None
    allow_comments: bool | None = None
    allow_attachments: bool | None = None
    max_attachment_size_mb: int | None = None
    max_attachments_per_post: int | None = None
    sort_order: int | None = None
    template_id: str | None = None
    auto_archive_days: int | None = None
    notification_settings: NotificationConfig | None = None


class Board(BaseDocument):
    """게시판 문서.

    BR-BRD-001: 동일 테넌트 내 게시판명 중복 불가.
    """

    board_name: str = ""
    board_type: BoardType = BoardType.GENERAL
    scope: BoardScope = BoardScope.COMPANY
    scope_id: str | None = None
    description: str = ""
    categories: list[str] = Field(default_factory=list)
    is_active: bool = True
    allow_anonymous: bool = False
    allow_comments: bool = True
    allow_attachments: bool = True
    max_attachment_size_mb: int = 50
    max_attachments_per_post: int = 10
    sort_order: int = 0
    template_id: str | None = None
    auto_archive_days: int | None = None
    notification_settings: NotificationConfig = Field(
        default_factory=NotificationConfig,
    )
    deleted_at: str | None = None
