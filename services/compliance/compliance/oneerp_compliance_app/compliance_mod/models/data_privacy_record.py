"""개인정보 처리 기록부(DataPrivacyRecord) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class PrivacyStatus(StrEnum):
    """기록부 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class DataPrivacyRecordCreate(BaseModel):
    """개인정보 처리 기록부 생성 요청 스키마."""

    processing_purpose: str
    data_categories: list[str]
    data_subjects: str
    retention_period: str
    legal_basis: str
    processor: str | None = None
    transfer_to_third_party: bool = False
    dpo_review_date: date | None = None
    status: PrivacyStatus = PrivacyStatus.DRAFT


class DataPrivacyRecordUpdate(BaseModel):
    """개인정보 처리 기록부 수정 요청 스키마."""

    processing_purpose: str | None = None
    data_categories: list[str] | None = None
    data_subjects: str | None = None
    retention_period: str | None = None
    legal_basis: str | None = None
    processor: str | None = None
    transfer_to_third_party: bool | None = None
    dpo_review_date: date | None = None
    status: PrivacyStatus | None = None


class DataPrivacyRecord(BaseDocument):
    """개인정보 처리 기록부 문서."""

    processing_purpose: str = ""
    data_categories: list[str] | None = None
    data_subjects: str = ""
    retention_period: str = ""
    legal_basis: str = ""
    processor: str | None = None
    transfer_to_third_party: bool = False
    dpo_review_date: date | None = None
    status: PrivacyStatus = PrivacyStatus.DRAFT
