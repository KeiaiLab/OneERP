"""태스크 템플릿(TaskTemplate) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class TaskTemplateCreate(BaseModel):
    """태스크 템플릿 생성 요청 스키마."""

    template_name: str
    description: str = ""
    estimated_hours: Decimal = Decimal(0)
    dependencies: list[str] = Field(default_factory=list)


class TaskTemplateUpdate(BaseModel):
    """태스크 템플릿 수정 요청 스키마."""

    template_name: str | None = None
    description: str | None = None
    estimated_hours: Decimal | None = None
    dependencies: list[str] | None = None


class TaskTemplate(BaseDocument):
    """태스크 템플릿 문서."""

    template_name: str = ""
    description: str = ""
    estimated_hours: Decimal = Decimal(0)
    dependencies: list[str] = Field(default_factory=list)
