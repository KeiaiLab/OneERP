"""설문 응답(SurveyResponse) 문서 모델.

설문에 대한 개별 응답을 저장한다.
네이밍 규칙: SR-{TENANT}-{#####}
"""

from __future__ import annotations

from datetime import UTC, datetime

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class Answer(BaseModel):
    """답변 — 임베디드."""

    question_id: str = Field(description="질문 ID")
    selected_options: list[str] = Field(default_factory=list, description="선택한 option_id")
    text_value: str | None = Field(default=None, description="텍스트 답변")
    scale_value: int | None = Field(default=None, description="척도 값")
    matrix_values: dict[str, str] | None = Field(default=None, description="매트릭스 값")
    date_value: str | None = Field(default=None, description="날짜 답변")
    nps_value: int | None = Field(default=None, description="NPS 값 (0~10)")


class SurveyResponseCreate(BaseModel):
    """설문 응답 생성 요청 스키마."""

    survey_id: str = Field(description="설문 ID")
    respondent_id: str | None = Field(default=None, description="응답자 ID")
    respondent_department: str | None = Field(default=None, description="응답자 부서")
    respondent_role: str | None = Field(default=None, description="응답자 직급")
    answers: list[Answer] = Field(description="답변 목록")
    ip_hash: str | None = Field(default=None, description="IP 해시")


class SurveyResponseUpdate(BaseModel):
    """설문 응답 수정 요청 스키마."""

    answers: list[Answer] | None = None


class SurveyResponse(BaseDocument):
    """설문 응답 문서."""

    survey_id: str = ""
    respondent_id: str | None = None
    respondent_department: str | None = None
    respondent_role: str | None = None
    answers: list[Answer] = Field(default_factory=list)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(tz=UTC))
    ip_hash: str | None = None
