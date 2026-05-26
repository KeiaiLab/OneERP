"""설계 문서(EngineeringDocument) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class EngineeringDocumentStatus(StrEnum):
    """설계 문서 상태."""

    DRAFT = "draft"
    RELEASED = "released"
    OBSOLETE = "obsolete"


class EngineeringDocumentCreate(BaseModel):
    """설계 문서 생성 요청 스키마."""

    document_title: str
    document_type: str = ""
    item_code: str = ""
    version: str = "1.0"
    file_path: str = ""


class EngineeringDocumentUpdate(BaseModel):
    """설계 문서 수정 요청 스키마."""

    document_title: str | None = None
    document_type: str | None = None
    item_code: str | None = None
    version: str | None = None
    file_path: str | None = None


class EngineeringDocument(BaseDocument):
    """설계 문서 문서."""

    status: EngineeringDocumentStatus = Field(
        default=EngineeringDocumentStatus.DRAFT,
        description="설계 문서 상태",
    )
    document_title: str = ""
    document_type: str = ""
    item_code: str = ""
    version: str = "1.0"
    file_path: str = ""
