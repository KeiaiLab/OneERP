"""연결 대상 그룹(ConsolidationGroup) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ConsolidationGroupCreate(BaseModel):
    """연결 대상 그룹 생성 요청 스키마."""

    group_name: str
    company_codes: list[str] = Field(default_factory=list)
    is_active: bool = True


class ConsolidationGroupUpdate(BaseModel):
    """연결 대상 그룹 수정 요청 스키마."""

    group_name: str | None = None
    company_codes: list[str] | None = None
    is_active: bool | None = None


class ConsolidationGroup(BaseDocument):
    """연결 대상 그룹 문서."""

    group_name: str = ""
    company_codes: list[str] = Field(default_factory=list)
    is_active: bool = True
