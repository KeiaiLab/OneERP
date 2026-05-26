"""BOM 개정(BomRevision) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class BOMRevisionStatus(StrEnum):
    """BOM 개정 상태."""

    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    OBSOLETE = "obsolete"


class BomRevisionCreate(BaseModel):
    """BOM 개정 생성 요청 스키마."""

    bom_id: str
    revision_no: int = 1
    change_description: str = ""
    effective_date: date | None = None


class BomRevisionUpdate(BaseModel):
    """BOM 개정 수정 요청 스키마."""

    bom_id: str | None = None
    revision_no: int | None = None
    change_description: str | None = None
    effective_date: date | None = None


class BOMRevision(BaseDocument):
    """BOM 개정 문서."""

    status: BOMRevisionStatus = Field(
        default=BOMRevisionStatus.DRAFT,
        description="BOM 개정 상태",
    )
    bom_id: str = ""
    revision_no: int = 1
    change_description: str = ""
    effective_date: date | None = None
