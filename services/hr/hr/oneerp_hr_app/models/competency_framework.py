"""역량 프레임워크(CompetencyFramework) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class CompetencyFrameworkCreate(BaseModel):
    """역량 프레임워크 생성 요청 스키마."""

    framework_name: str
    description: str = ""
    competencies: list[str] = Field(default_factory=list)
    is_active: bool = True


class CompetencyFrameworkUpdate(BaseModel):
    """역량 프레임워크 수정 요청 스키마."""

    framework_name: str | None = None
    description: str | None = None
    competencies: list[str] | None = None
    is_active: bool | None = None


class CompetencyFramework(BaseDocument):
    """역량 프레임워크 문서."""

    framework_name: str = ""
    description: str = ""
    competencies: list[str] = Field(default_factory=list)
    is_active: bool = True
