"""개인정보 처리 기록(DataPrivacyRecord) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class DataPrivacyRecordStatus(StrEnum):
    """개인정보 처리 기록 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class DataPrivacyRecordCreate(BaseModel):
    """개인정보 처리 기록 생성 요청 스키마."""

    data_subject: str
    processing_purpose: str = ""
    data_categories: list[str] = Field(default_factory=list)
    retention_period: str = ""
    legal_basis: str = ""


class DataPrivacyRecordUpdate(BaseModel):
    """개인정보 처리 기록 수정 요청 스키마."""

    data_subject: str | None = None
    processing_purpose: str | None = None
    data_categories: list[str] | None = None
    retention_period: str | None = None
    legal_basis: str | None = None


class DataPrivacyRecord(BaseDocument):
    """개인정보 처리 기록 문서."""

    status: DataPrivacyRecordStatus = Field(
        default=DataPrivacyRecordStatus.DRAFT,
        description="개인정보 처리 기록 상태",
    )
    data_subject: str = ""
    processing_purpose: str = ""
    data_categories: list[str] = Field(default_factory=list)
    retention_period: str = ""
    legal_basis: str = ""
