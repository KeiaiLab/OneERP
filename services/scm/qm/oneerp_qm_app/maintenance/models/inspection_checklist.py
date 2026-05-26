"""점검체크리스트(InspectionChecklist) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ChecklistItem(BaseModel):
    """체크리스트 항목."""

    idx: int = 0
    item_name: str = ""
    description: str = ""
    inspection_method: str = ""
    acceptance_criteria: str = ""
    is_required: bool = True


class InspectionChecklistCreate(BaseModel):
    """점검체크리스트 생성 요청 스키마."""

    checklist_name: str
    equipment_category: str = ""
    description: str = ""
    items: list[ChecklistItem] = Field(default_factory=list)
    is_active: bool = True


class InspectionChecklistUpdate(BaseModel):
    """점검체크리스트 수정 요청 스키마."""

    checklist_name: str | None = None
    equipment_category: str | None = None
    description: str | None = None
    items: list[ChecklistItem] | None = None
    is_active: bool | None = None


class InspectionChecklist(BaseDocument):
    """점검체크리스트 문서."""

    checklist_name: str = ""
    equipment_category: str = ""
    description: str = ""
    items: list[ChecklistItem] = Field(default_factory=list)
    is_active: bool = True
