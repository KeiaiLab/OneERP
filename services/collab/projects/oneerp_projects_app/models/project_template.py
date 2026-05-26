"""프로젝트 템플릿(ProjectTemplate) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class ProjectTemplateCreate(BaseModel):
    """프로젝트 템플릿 생성 요청 스키마."""

    template_name: str
    description: str = ""
    default_tasks: list[str] = Field(default_factory=list)
    estimated_days: int = 0


class ProjectTemplateUpdate(BaseModel):
    """프로젝트 템플릿 수정 요청 스키마."""

    template_name: str | None = None
    description: str | None = None
    default_tasks: list[str] | None = None
    estimated_days: int | None = None


class ProjectTemplate(BaseDocument):
    """프로젝트 템플릿 문서."""

    template_name: str = ""
    description: str = ""
    default_tasks: list[str] = Field(default_factory=list)
    estimated_days: int = 0
