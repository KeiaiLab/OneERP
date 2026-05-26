"""문서 관리(Document) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class DocumentStatus(StrEnum):
    """문서 관리 상태."""

    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DocumentCreate(BaseModel):
    """문서 관리 생성 요청 스키마."""

    document_title: str
    document_type: str = ""
    file_path: str = ""
    file_size: int = 0
    uploaded_by: str = ""


class DocumentUpdate(BaseModel):
    """문서 관리 수정 요청 스키마."""

    document_title: str | None = None
    document_type: str | None = None
    file_path: str | None = None
    file_size: int | None = None
    uploaded_by: str | None = None


class Document(BaseDocument):
    """문서 관리 문서."""

    status: DocumentStatus = Field(
        default=DocumentStatus.DRAFT,
        description="문서 관리 상태",
    )
    document_title: str = ""
    document_type: str = ""
    file_path: str = ""
    file_size: int = 0
    uploaded_by: str = ""
