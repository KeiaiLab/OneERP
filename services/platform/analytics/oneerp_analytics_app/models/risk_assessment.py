"""리스크 평가(RiskAssessment) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class RiskAssessmentStatus(StrEnum):
    """리스크 평가 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"


class RiskAssessmentCreate(BaseModel):
    """리스크 평가 생성 요청 스키마."""

    risk_name: str
    category: str = ""
    likelihood: int = 0
    impact: int = 0
    risk_score: Decimal = Decimal(0)
    mitigation: str = ""


class RiskAssessmentUpdate(BaseModel):
    """리스크 평가 수정 요청 스키마."""

    risk_name: str | None = None
    category: str | None = None
    likelihood: int | None = None
    impact: int | None = None
    risk_score: Decimal | None = None
    mitigation: str | None = None


class RiskAssessment(BaseDocument):
    """리스크 평가 문서."""

    status: RiskAssessmentStatus = Field(
        default=RiskAssessmentStatus.DRAFT,
        description="리스크 평가 상태",
    )
    risk_name: str = ""
    category: str = ""
    likelihood: int = 0
    impact: int = 0
    risk_score: Decimal = Decimal(0)
    mitigation: str = ""
