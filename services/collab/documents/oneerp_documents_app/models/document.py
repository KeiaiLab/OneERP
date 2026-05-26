"""문서(Document) 모델 — 기업 전자문서의 핵심 엔티티.

BR-DOC-001: 문서번호 자동 부여 (DOC-{YYYY}-{#####}).
BR-DOC-002: 카테고리 필수 지정.
BR-DOC-004: 보안 등급 상속.
BR-DOC-005: 기밀 문서 다운로드 제한.
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import datetime


class DocumentStatus(StrEnum):
    """문서 상태."""

    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    DISPOSED = "disposed"


class SecurityLevel(StrEnum):
    """보안 등급."""

    TOP_SECRET = "top_secret"  # noqa: S105
    CONFIDENTIAL = "confidential"
    INTERNAL = "internal"
    PUBLIC = "public"


class FileAttachment(BaseModel):
    """첨부파일 임베디드 모델."""

    file_id: str = ""
    file_name: str = ""
    file_size: int = 0
    mime_type: str = ""
    storage_path: str = ""
    checksum: str = ""
    uploaded_at: datetime | None = None
    uploaded_by: str = ""


class DocumentCreate(BaseModel):
    """문서 생성 요청 스키마."""

    title: str = Field(min_length=1, max_length=500, description="문서 제목")
    category: str = Field(min_length=1, description="문서 분류 ID")
    content: str = Field(default="", description="리치텍스트 HTML 내용")
    template_id: str | None = Field(default=None, description="템플릿 ID")
    template_variables: dict[str, str] = Field(
        default_factory=dict, description="템플릿 변수 바인딩"
    )
    security_level: SecurityLevel = Field(default=SecurityLevel.INTERNAL, description="보안 등급")
    tags: list[str] = Field(default_factory=list, description="태그 목록")
    metadata: dict[str, object] = Field(default_factory=dict, description="확장 메타데이터")
    department: str = Field(default="", description="소속 부서")
    company: str = Field(default="", description="회사 ID")
    summary: str = Field(default="", max_length=2000, description="문서 요약")


class DocumentUpdate(BaseModel):
    """문서 수정 요청 스키마."""

    title: str | None = None
    content: str | None = None
    category: str | None = None
    security_level: SecurityLevel | None = None
    tags: list[str] | None = None
    metadata: dict[str, object] | None = None
    department: str | None = None
    summary: str | None = None
    change_summary: str = Field(default="", description="변경 사항 요약")


class Document(BaseDocument):
    """문서 엔티티.

    기업의 모든 전자문서를 표현하는 핵심 모델.
    리치텍스트 콘텐츠 또는 파일 첨부 기반 문서를 통합 관리한다.
    """

    company: str = ""
    doc_no: str = ""
    title: str = ""
    category: str = ""
    content: str = ""
    content_plain: str = ""
    summary: str = ""
    file_attachments: list[FileAttachment] = Field(default_factory=list)
    author: str = ""
    department: str = ""
    version: int = 1
    status: DocumentStatus = DocumentStatus.DRAFT
    security_level: SecurityLevel = SecurityLevel.INTERNAL
    retention_policy: str | None = None
    retention_until: datetime | None = None
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    template_id: str | None = None
    approval_request_id: str | None = None
    source_module: str | None = None
    source_document_id: str | None = None
    is_locked: bool = False
    locked_by: str | None = None
    locked_at: datetime | None = None
    download_restricted: bool = False
    watermark_enabled: bool = False
    is_deleted: bool = False
    deleted_at: datetime | None = None
    deleted_by: str | None = None
