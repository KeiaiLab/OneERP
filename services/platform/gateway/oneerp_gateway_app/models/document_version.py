"""문서 버전(DocumentVersion) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class DocumentVersionCreate(BaseModel):
    """문서 버전 생성 요청 스키마."""

    document_id: str
    version_no: int = 1
    change_description: str = ""
    modified_by: str = ""


class DocumentVersionUpdate(BaseModel):
    """문서 버전 수정 요청 스키마."""

    document_id: str | None = None
    version_no: int | None = None
    change_description: str | None = None
    modified_by: str | None = None


class DocumentVersion(BaseDocument):
    """문서 버전 문서."""

    document_id: str = ""
    version_no: int = 1
    change_description: str = ""
    modified_by: str = ""
