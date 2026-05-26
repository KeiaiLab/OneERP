"""수익인식 규칙(RevenueRecognitionRule) 문서 모델."""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class RevenueRecognitionRuleStatus(StrEnum):
    """수익인식 규칙 상태."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class RevenueRecognitionRuleCreate(BaseModel):
    """수익인식 규칙 생성 요청 스키마."""

    rule_name: str
    recognition_method: str = ""
    period_months: int = 0
    is_active: bool = True


class RevenueRecognitionRuleUpdate(BaseModel):
    """수익인식 규칙 수정 요청 스키마."""

    rule_name: str | None = None
    recognition_method: str | None = None
    period_months: int | None = None
    is_active: bool | None = None


class RevenueRecognitionRule(BaseDocument):
    """수익인식 규칙 문서."""

    status: RevenueRecognitionRuleStatus = Field(
        default=RevenueRecognitionRuleStatus.ACTIVE,
        description="수익인식 규칙 상태",
    )
    rule_name: str = ""
    recognition_method: str = ""
    period_months: int = 0
    is_active: bool = True
