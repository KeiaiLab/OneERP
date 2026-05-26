"""설문 템플릿(SurveyTemplate) 문서 모델.

자주 사용하는 설문을 템플릿으로 저장하고 재사용한다.
네이밍 규칙: ST-{TENANT}-{#####}
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class TemplateCategory(StrEnum):
    """템플릿 카테고리."""

    SATISFACTION = "satisfaction"
    CULTURE = "culture"
    EDUCATION = "education"
    STRESS = "stress"
    CUSTOM = "custom"


class TemplateQuestionSnapshot(BaseModel):
    """템플릿 내 질문 스냅샷 — 임베디드."""

    question_text: str = Field(description="질문 내용")
    question_type: str = Field(description="질문 유형")
    required: bool = Field(default=True, description="필수 여부")
    order: int = Field(ge=1, description="표시 순서")
    options: list[dict[str, str | int | bool]] = Field(default_factory=list, description="선택지")
    scale_min: int = Field(default=1, description="척도 최솟값")
    scale_max: int = Field(default=5, description="척도 최댓값")
    matrix_rows: list[str] = Field(default_factory=list, description="매트릭스 행")
    matrix_columns: list[str] = Field(default_factory=list, description="매트릭스 열")


class SurveyTemplateCreate(BaseModel):
    """설문 템플릿 생성 요청 스키마."""

    name: str = Field(min_length=1, max_length=200, description="템플릿명")
    category: TemplateCategory = Field(description="카테고리")
    description: str = Field(default="", description="설명")
    questions: list[TemplateQuestionSnapshot] = Field(min_length=1, description="질문 목록")
    is_system: bool = Field(default=False, description="시스템 기본 템플릿 여부")


class SurveyTemplateUpdate(BaseModel):
    """설문 템플릿 수정 요청 스키마."""

    name: str | None = None
    category: TemplateCategory | None = None
    description: str | None = None
    questions: list[TemplateQuestionSnapshot] | None = None


class SurveyTemplate(BaseDocument):
    """설문 템플릿 문서."""

    name: str = ""
    category: TemplateCategory = TemplateCategory.CUSTOM
    description: str = ""
    questions: list[TemplateQuestionSnapshot] = Field(default_factory=list)
    is_system: bool = False
    usage_count: int = 0
