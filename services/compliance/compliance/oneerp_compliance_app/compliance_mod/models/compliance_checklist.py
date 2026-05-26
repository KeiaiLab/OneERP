"""준�� 체크리스트(ComplianceChecklist) 문서 모델."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class ChecklistStatus(StrEnum):
    """체크리스트 상태."""

    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ComplianceChecklistCreate(BaseModel):
    """준수 체크리스트 생성 요청 스키마."""

    name: str
    internal_control: str
    period: str
    items: list[dict[str, Any]]
    completed_by: str | None = None
    reviewed_by: str | None = None
    status: ChecklistStatus = ChecklistStatus.DRAFT
    company: str = ""


class ComplianceChecklistUpdate(BaseModel):
    """준수 체크리스트 수정 요청 스키마."""

    name: str | None = None
    internal_control: str | None = None
    period: str | None = None
    items: list[dict[str, Any]] | None = None
    completed_by: str | None = None
    reviewed_by: str | None = None
    status: ChecklistStatus | None = None
    company: str | None = None


class ComplianceChecklist(BaseDocument):
    """준수 체크리스트 ���서."""

    name: str = ""
    internal_control: str = ""
    period: str = ""
    items: list[dict[str, Any]] | None = None
    completed_by: str | None = None
    reviewed_by: str | None = None
    status: ChecklistStatus = ChecklistStatus.DRAFT
    company: str = ""
