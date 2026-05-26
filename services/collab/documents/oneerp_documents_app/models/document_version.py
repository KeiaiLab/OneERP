"""문서 버전(DocumentVersion) 모델 — 문서 변경 이력 스냅샷.

BR-DOC-006: 내용/첨부 변경 시 minor 버전 자동 생성.
BR-DOC-007: 배포/승인 시 major 버전 자동 생성.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from .document import FileAttachment


class DocumentVersionCreate(BaseModel):
    """문서 버전 생성 요청 스키마."""

    document_id: str = Field(description="문서 참조 ID")
    version_no: int = Field(ge=1, description="버전 번호")
    version_type: str = Field(default="minor", description="버전 유형 (major/minor)")
    title: str = Field(default="", description="제목 스냅샷")
    content: str = Field(default="", description="내용 스냅샷")
    file_attachments: list[FileAttachment] = Field(default_factory=list)
    change_summary: str = Field(default="", description="변경 사항 요약")
    changed_by: str = Field(default="", description="변경자")
    content_hash: str = Field(default="", description="내용 해시 (SHA-256)")
    metadata_snapshot: dict[str, object] = Field(default_factory=dict)


class DocumentVersionUpdate(BaseModel):
    """문서 버전 수정 스키마 (일반적으로 사용하지 않음)."""

    change_summary: str | None = None


class DocumentVersion(BaseDocument):
    """문서 버전 엔티티.

    문서의 모든 변경 이력을 기록하여 특정 시점 복원을 지원한다.
    """

    document_id: str = ""
    version_no: int = 1
    version_type: str = "minor"
    title: str = ""
    content: str = ""
    file_attachments: list[FileAttachment] = Field(default_factory=list)
    change_summary: str = ""
    changed_by: str = ""
    content_hash: str = ""
    metadata_snapshot: dict[str, object] = Field(default_factory=dict)
