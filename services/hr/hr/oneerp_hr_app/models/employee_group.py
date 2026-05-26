"""직원 그룹(EmployeeGroup) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class EmployeeGroupCreate(BaseModel):
    """직원 그룹 생성 요청 스키마."""

    group_name: str
    description: str = ""
    member_ids: list[str] = Field(default_factory=list)


class EmployeeGroupUpdate(BaseModel):
    """직원 그룹 수정 요청 스키마."""

    group_name: str | None = None
    description: str | None = None
    member_ids: list[str] | None = None


class EmployeeGroup(BaseDocument):
    """직원 그룹 문서."""

    group_name: str = ""
    description: str = ""
    member_ids: list[str] = Field(default_factory=list)
