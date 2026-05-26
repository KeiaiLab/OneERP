"""예방보전계획(PreventiveMaintenancePlan) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class PreventiveMaintenancePlanCreate(BaseModel):
    """예방보전계획 생성 요청 스키마."""

    plan_name: str
    equipment_id: str
    maintenance_type_id: str = ""
    interval_days: int = 30
    start_date: date | None = None
    end_date: date | None = None
    assigned_team: str = ""
    description: str = ""
    checklist_ids: list[str] = Field(default_factory=list)
    is_active: bool = True


class PreventiveMaintenancePlanUpdate(BaseModel):
    """예방보전계획 수정 요청 스키마."""

    plan_name: str | None = None
    equipment_id: str | None = None
    maintenance_type_id: str | None = None
    interval_days: int | None = None
    start_date: date | None = None
    end_date: date | None = None
    assigned_team: str | None = None
    description: str | None = None
    checklist_ids: list[str] | None = None
    is_active: bool | None = None


class PreventiveMaintenancePlan(BaseDocument):
    """예방보전계획 문서."""

    plan_name: str = ""
    equipment_id: str = ""
    maintenance_type_id: str = ""
    interval_days: int = 30
    start_date: date | None = None
    end_date: date | None = None
    assigned_team: str = ""
    description: str = ""
    checklist_ids: list[str] = Field(default_factory=list)
    is_active: bool = True
    last_execution_date: date | None = None
    next_due_date: date | None = None
