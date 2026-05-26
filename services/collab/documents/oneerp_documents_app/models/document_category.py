"""문서 분류(DocumentCategory) 모델 — 계층형 문서 분류 체계.

BR-DOC-018: 소속 문서 존재 시 삭제 제한.
BR-DOC-019: 최대 10단계 계층 깊이 제한.
"""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class DocumentCategoryCreate(BaseModel):
    """문서 분류 생성 요청 스키마."""

    name: str = Field(min_length=1, max_length=200, description="분류명")
    code: str = Field(min_length=3, max_length=20, description="분류 코드")
    company: str = Field(default="", description="회사 ID")
    parent_category: str | None = Field(default=None, description="상위 분류 ID")
    description: str = Field(default="", max_length=1000, description="설명")
    default_retention_policy: str | None = Field(default=None)
    default_security_level: str = Field(default="internal")
    metadata_schema: dict[str, object] = Field(default_factory=dict)
    sort_order: int = Field(default=0)


class DocumentCategoryUpdate(BaseModel):
    """문서 분류 수정 요청 스키마."""

    name: str | None = None
    description: str | None = None
    default_retention_policy: str | None = None
    default_security_level: str | None = None
    metadata_schema: dict[str, object] | None = None
    sort_order: int | None = None
    is_active: bool | None = None


class DocumentCategory(BaseDocument):
    """문서 분류 엔티티.

    계층형 문서 분류 체계를 정의한다. 최대 10단계 계층 지원.
    """

    company: str = ""
    name: str = ""
    code: str = ""
    parent_category: str | None = None
    depth: int = 0
    path: str = ""
    description: str = ""
    default_retention_policy: str | None = None
    default_security_level: str = "internal"
    metadata_schema: dict[str, object] = Field(default_factory=dict)
    sort_order: int = 0
    is_active: bool = True
    is_deleted: bool = False
    document_count: int = 0
