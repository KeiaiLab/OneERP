"""자산 유지보수 계획(AssetMaintenancePlan) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class AssetMaintenancePlanCreate(BaseModel):
    """자산 유지보수 계획 생성 요청 스키마."""

    plan_name: str
    asset_category: str = ""
    frequency: str = ""
    checklist: list[str] = Field(default_factory=list)
    is_active: bool = True


class AssetMaintenancePlanUpdate(BaseModel):
    """자산 유지보수 계획 수정 요청 스키마."""

    plan_name: str | None = None
    asset_category: str | None = None
    frequency: str | None = None
    checklist: list[str] | None = None
    is_active: bool | None = None


class AssetMaintenancePlan(BaseDocument):
    """자산 유지보수 계획 문서."""

    plan_name: str = ""
    asset_category: str = ""
    frequency: str = ""
    checklist: list[str] = Field(default_factory=list)
    is_active: bool = True
