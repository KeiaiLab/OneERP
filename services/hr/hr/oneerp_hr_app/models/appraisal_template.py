"""인사 평가 템플릿(AppraisalTemplate) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class AppraisalTemplateCreate(BaseModel):
    """인사 평가 템플릿 생성 요청 스키마."""

    template_name: str
    criteria: list[str] = Field(default_factory=list)
    max_score: Decimal = Decimal(100)


class AppraisalTemplateUpdate(BaseModel):
    """인사 평가 템플릿 수정 요청 스키마."""

    template_name: str | None = None
    criteria: list[str] | None = None
    max_score: Decimal | None = None


class AppraisalTemplate(BaseDocument):
    """인사 평가 템플릿 문서."""

    template_name: str = ""
    criteria: list[str] = Field(default_factory=list)
    max_score: Decimal = Decimal(100)
