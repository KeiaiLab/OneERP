"""역량 체계(CompetencyFramework) 문서 모델."""

from __future__ import annotations

from typing import Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CompetencyFrameworkCreate(BaseModel):
    """역량 체계 생성 요청 스키마."""

    framework_name: str
    job_family: str = ""
    competencies: list[dict[str, Any]] = []
    proficiency_levels: list[dict[str, Any]] = []


class CompetencyFrameworkUpdate(BaseModel):
    """역량 체계 수정 요청 스키마."""

    framework_name: str | None = None
    job_family: str | None = None
    competencies: list[dict[str, Any]] | None = None
    proficiency_levels: list[dict[str, Any]] | None = None


class CompetencyFramework(BaseDocument):
    """역량 체계 문서."""

    framework_name: str = ""
    job_family: str = ""
    competencies: list[dict[str, Any]] = []
    proficiency_levels: list[dict[str, Any]] = []
