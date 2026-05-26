"""내부 통제(InternalControl) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class InternalControlStatus(StrEnum):
    """내부 통제 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class InternalControlCreate(BaseModel):
    """내부 통제 생성 요청 스키마."""

    control_name: str
    control_type: str = ""
    responsible: str = ""
    frequency: str = ""
    is_active: bool = True


class InternalControlUpdate(BaseModel):
    """내부 통제 수정 요청 스키마."""

    control_name: str | None = None
    control_type: str | None = None
    responsible: str | None = None
    frequency: str | None = None
    is_active: bool | None = None


class InternalControl(BaseDocument):
    """내부 통제 문서."""

    status: InternalControlStatus = Field(
        default=InternalControlStatus.DRAFT,
        description="내부 통제 상태",
    )
    control_name: str = ""
    control_type: str = ""
    responsible: str = ""
    frequency: str = ""
    is_active: bool = True
