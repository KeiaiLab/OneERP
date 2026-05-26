"""설문 응답(SurveyResponse) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class SurveyResponseCreate(BaseModel):
    """설문 응답 생성 요청 스키마."""

    survey_id: str
    respondent: str = ""
    response_date: date | None = None
    answers: str = ""
    score: Decimal = Decimal(0)


class SurveyResponseUpdate(BaseModel):
    """설문 응답 수정 요청 스키마."""

    survey_id: str | None = None
    respondent: str | None = None
    response_date: date | None = None
    answers: str | None = None
    score: Decimal | None = None


class SurveyResponse(BaseDocument):
    """설문 응답 문서."""

    survey_id: str = ""
    respondent: str = ""
    response_date: date | None = None
    answers: str = ""
    score: Decimal = Decimal(0)
