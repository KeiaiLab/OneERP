"""위험 평가(RiskAssessment) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class RiskCategory(StrEnum):
    """위험 분류."""

    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    COMPLIANCE = "compliance"
    STRATEGIC = "strategic"


class RiskStatus(StrEnum):
    """위험 평가 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"


class RiskAssessmentCreate(BaseModel):
    """위험 평가 생성 요청 스키마."""

    risk_name: str
    risk_category: RiskCategory
    likelihood: int
    impact: int
    risk_score: int
    mitigation: str | None = None
    owner: str = ""
    status: RiskStatus = RiskStatus.DRAFT
    company: str = ""


class RiskAssessmentUpdate(BaseModel):
    """위험 평가 수정 요청 스키마."""

    risk_name: str | None = None
    risk_category: RiskCategory | None = None
    likelihood: int | None = None
    impact: int | None = None
    risk_score: int | None = None
    mitigation: str | None = None
    owner: str | None = None
    status: RiskStatus | None = None
    company: str | None = None


class RiskAssessment(BaseDocument):
    """위험 평가 문서."""

    risk_name: str = ""
    risk_category: RiskCategory = RiskCategory.OPERATIONAL
    likelihood: int = 1
    impact: int = 1
    risk_score: int = 1
    mitigation: str | None = None
    owner: str = ""
    status: RiskStatus = RiskStatus.DRAFT
    company: str = ""
