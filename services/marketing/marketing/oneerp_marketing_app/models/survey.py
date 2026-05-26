"""설문조사 모델 — 마케팅 설문을 관리한다."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date, datetime


class SurveyQuestion(BaseModel):
    """설문 질문."""

    question_type: str = "text"  # text/choice/rating/boolean
    text: str = ""
    options: list[str] = []
    required: bool = False


class SurveyCreate(BaseModel):
    """설문조사 생성 요청 스키마."""

    title: str
    description: str = ""
    questions: list[SurveyQuestion] = []
    target_audience_id: str = ""
    start_date: date | None = None
    end_date: date | None = None
    company: str = ""


class SurveyUpdate(BaseModel):
    """설문조사 수정 요청 스키마."""

    title: str | None = None
    description: str | None = None
    questions: list[SurveyQuestion] | None = None
    status: str | None = None
    end_date: date | None = None


class Survey(BaseDocument):
    """설문조사 문서 — 마케팅 설문 상세 정보를 저장한다."""

    title: str = ""
    description: str = ""
    questions: list[SurveyQuestion] = []
    target_audience_id: str = ""
    start_date: date | None = None
    end_date: date | None = None
    response_count: int = 0
    status: str = "draft"  # draft/published/closed
    company: str = ""


class SurveyAnswer(BaseModel):
    """설문 응답 항목."""

    question_idx: int = 0
    answer: Any = None


class SurveyResponseCreate(BaseModel):
    """설문 응답 생성 요청 스키마."""

    survey_id: str
    respondent_id: str = ""
    answers: list[SurveyAnswer] = []


class SurveyResponseUpdate(BaseModel):
    """설문 응답 수정 요청 스키마."""

    answers: list[SurveyAnswer] | None = None


class SurveyResponse(BaseDocument):
    """설문 응답 문서 — 개별 설문 응답을 저장한다."""

    survey_id: str = ""
    respondent_id: str = ""
    answers: list[SurveyAnswer] = []
    submitted_at: datetime | None = None
