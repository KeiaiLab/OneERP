"""업무일지 템플릿(WorkReportTemplate) 모델 — 반복 업무일지 자동 생성용.

비즈니스 규칙:
- BR-WR-010: 템플릿명은 필수
- BR-WR-011: 템플릿 항목은 최소 1개 이상
"""

from __future__ import annotations

from typing import Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

from .work_report import WorkReportCategory


class WorkReportTemplateCreate(BaseModel):
    """업무일지 템플릿 생성 요청 스키마.

    BR-WR-010: 템플릿명(name) 필수.
    """

    name: str
    description: str = ""
    category: WorkReportCategory = WorkReportCategory.DAILY
    department: str = ""
    default_items: list[dict[str, Any]] = Field(default_factory=list)
    is_active: bool = True


class WorkReportTemplateUpdate(BaseModel):
    """업무일지 템플릿 수정 요청 스키마."""

    name: str | None = None
    description: str | None = None
    category: WorkReportCategory | None = None
    department: str | None = None
    default_items: list[dict[str, Any]] | None = None
    is_active: bool | None = None


class WorkReportTemplate(BaseDocument):
    """업무일지 템플릿 문서 — 마스터 데이터.

    naming prefix: WRT
    """

    name: str = Field(default="", description="템플릿명")
    description: str = Field(default="", description="설명")
    category: WorkReportCategory = Field(default=WorkReportCategory.DAILY, description="카테고리")
    department: str = Field(default="", description="대상 부서")
    default_items: list[dict[str, Any]] = Field(default_factory=list, description="기본 업무 항목")
    is_active: bool = Field(default=True, description="활성 여부")
