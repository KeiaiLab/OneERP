"""설문 질문(SurveyQuestion) 문서 모델.

설문의 개별 질문을 정의한다. 질문 유형, 선택지, 조건부 로직을 관리한다.
네이밍 규칙: SQ-{TENANT}-{#####}
"""

from __future__ import annotations

from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class QuestionType(StrEnum):
    """질문 유형."""

    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TEXT = "text"
    LONG_TEXT = "long_text"
    SCALE = "scale"
    MATRIX = "matrix"
    NPS = "nps"
    DATE = "date"


class LogicAction(StrEnum):
    """조건부 로직 액션."""

    JUMP_TO = "jump_to"
    SKIP = "skip"
    END_SURVEY = "end_survey"


class QuestionOption(BaseModel):
    """질문 선택지 — 임베디드."""

    option_id: str = Field(description="선택지 ID")
    text: str = Field(description="선택지 텍스트")
    order: int = Field(description="표시 순서")
    is_other: bool = Field(default=False, description="기타 옵션 여부")


class LogicRule(BaseModel):
    """조건부 로직 규칙 — 임베디드."""

    condition_option_id: str = Field(description="조건 선택지 ID")
    action: LogicAction = Field(description="액션")
    target_question_id: str | None = Field(default=None, description="이동 대상 질문 ID")


class SurveyQuestionCreate(BaseModel):
    """설문 질문 생성 요청 스키마."""

    survey_id: str = Field(description="설문 ID")
    question_text: str = Field(min_length=1, max_length=1000, description="질문 내용")
    question_type: QuestionType = Field(description="질문 유형")
    required: bool = Field(default=True, description="필수 응답 여부")
    order: int = Field(ge=1, description="표시 순서")
    options: list[QuestionOption] = Field(default_factory=list, description="선택지")
    scale_min: int = Field(default=1, description="척도 최솟값")
    scale_max: int = Field(default=5, le=10, description="척도 최댓값")
    scale_min_label: str = Field(default="", description="척도 최솟값 레이블")
    scale_max_label: str = Field(default="", description="척도 최댓값 레이블")
    matrix_rows: list[str] = Field(default_factory=list, description="매트릭스 행 목록")
    matrix_columns: list[str] = Field(default_factory=list, description="매트릭스 열 목록")
    logic_rules: list[LogicRule] = Field(default_factory=list, description="조건부 로직")


class SurveyQuestionUpdate(BaseModel):
    """설문 질문 수정 요청 스키마."""

    question_text: str | None = None
    required: bool | None = None
    order: int | None = None
    options: list[QuestionOption] | None = None
    scale_min: int | None = None
    scale_max: int | None = None
    scale_min_label: str | None = None
    scale_max_label: str | None = None
    matrix_rows: list[str] | None = None
    matrix_columns: list[str] | None = None
    logic_rules: list[LogicRule] | None = None


class SurveyQuestion(BaseDocument):
    """설문 질문 문서."""

    survey_id: str = ""
    question_text: str = ""
    question_type: QuestionType = QuestionType.TEXT
    required: bool = True
    order: int = 1
    options: list[QuestionOption] = Field(default_factory=list)
    scale_min: int = 1
    scale_max: int = 5
    scale_min_label: str = ""
    scale_max_label: str = ""
    matrix_rows: list[str] = Field(default_factory=list)
    matrix_columns: list[str] = Field(default_factory=list)
    logic_rules: list[LogicRule] = Field(default_factory=list)
