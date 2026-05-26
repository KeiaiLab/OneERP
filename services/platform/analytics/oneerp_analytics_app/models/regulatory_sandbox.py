"""규제 샌드박스(RegulatorySandbox) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class RegulatorySandboxStatus(StrEnum):
    """규제 샌드박스 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    EXPIRED = "expired"


class RegulatorySandboxCreate(BaseModel):
    """규제 샌드박스 생성 요청 스키마."""

    sandbox_name: str
    regulation: str = ""
    start_date: date | None = None
    end_date: date | None = None
    description: str = ""


class RegulatorySandboxUpdate(BaseModel):
    """규제 샌드박스 수정 요청 스키마."""

    sandbox_name: str | None = None
    regulation: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    description: str | None = None


class RegulatorySandbox(BaseDocument):
    """규제 샌드박스 문서."""

    status: RegulatorySandboxStatus = Field(
        default=RegulatorySandboxStatus.DRAFT,
        description="규제 샌드박스 상태",
    )
    sandbox_name: str = ""
    regulation: str = ""
    start_date: date | None = None
    end_date: date | None = None
    description: str = ""
