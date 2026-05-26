"""규제 샌드박스(RegulatorySandbox) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class SandboxType(StrEnum):
    """샌드박스 유형."""

    FINANCIAL = "financial"
    INDUSTRIAL = "industrial"
    ICT = "ict"


class SandboxStatus(StrEnum):
    """샌드박스 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"


class RegulatorySandboxCreate(BaseModel):
    """규제 ��드박스 생성 요청 스키마."""

    sandbox_type: SandboxType
    project_name: str
    approval_date: date
    expiry_date: date
    regulatory_body: str
    exempted_regulations: list[str]
    status: SandboxStatus = SandboxStatus.DRAFT
    review_notes: str | None = None


class RegulatorySandboxUpdate(BaseModel):
    """규제 샌���박스 수정 요청 스키마."""

    sandbox_type: SandboxType | None = None
    project_name: str | None = None
    approval_date: date | None = None
    expiry_date: date | None = None
    regulatory_body: str | None = None
    exempted_regulations: list[str] | None = None
    status: SandboxStatus | None = None
    review_notes: str | None = None


class RegulatorySandbox(BaseDocument):
    """규제 샌드박스 문서."""

    sandbox_type: SandboxType = SandboxType.FINANCIAL
    project_name: str = ""
    approval_date: date | None = None
    expiry_date: date | None = None
    regulatory_body: str = ""
    exempted_regulations: list[str] | None = None
    status: SandboxStatus = SandboxStatus.DRAFT
    review_notes: str | None = None
