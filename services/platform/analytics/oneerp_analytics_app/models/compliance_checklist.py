"""컴플라이언스 체크리스트(ComplianceChecklist) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ComplianceChecklistStatus(StrEnum):
    """컴플라이언스 체크리스트 상태."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ComplianceChecklistCreate(BaseModel):
    """컴플라이언스 체크리스트 생성 요청 스키마."""

    checklist_name: str
    regulation: str = ""
    items: list[str] = Field(default_factory=list)
    is_completed: bool = False


class ComplianceChecklistUpdate(BaseModel):
    """컴플라이언스 체크리스트 수정 요청 스키마."""

    checklist_name: str | None = None
    regulation: str | None = None
    items: list[str] | None = None
    is_completed: bool | None = None


class ComplianceChecklist(BaseDocument):
    """컴플라이언스 체크리스트 문서."""

    status: ComplianceChecklistStatus = Field(
        default=ComplianceChecklistStatus.DRAFT,
        description="컴플라이언스 체크리스트 상태",
    )
    checklist_name: str = ""
    regulation: str = ""
    items: list[str] = Field(default_factory=list)
    is_completed: bool = False
