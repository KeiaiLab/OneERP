"""설문(Survey) 문서 모델.

설문/투표의 최상위 단위. 제목, 설명, 설정(익명/기명/기간/대상), 상태를 관리한다.
네이밍 규칙: SVY-{TENANT}-{#####}
"""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field, model_validator

if TYPE_CHECKING:
    from datetime import datetime


class SurveyType(StrEnum):
    """설문 유형."""

    SURVEY = "survey"
    POLL = "poll"


class Anonymity(StrEnum):
    """익명/기명 구분."""

    ANONYMOUS = "anonymous"
    NAMED = "named"


class SurveyStatus(StrEnum):
    """설문 상태."""

    DRAFT = "draft"
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class TargetType(StrEnum):
    """배포 대상 유형."""

    ALL = "all"
    DEPARTMENT = "department"
    ROLE = "role"
    CUSTOM = "custom"


class ShowResults(StrEnum):
    """결과 공개 시점."""

    REALTIME = "realtime"
    AFTER_SUBMIT = "after_submit"
    AFTER_CLOSE = "after_close"
    NEVER = "never"


class SurveyCreate(BaseModel):
    """설문 생성 요청 스키마."""

    title: str = Field(min_length=1, max_length=500, description="설문 제목")
    description: str = Field(default="", max_length=2000, description="설문 설명")
    survey_type: SurveyType = Field(default=SurveyType.SURVEY, description="유형")
    anonymity: Anonymity = Field(default=Anonymity.NAMED, description="익명/기명")
    starts_at: datetime | None = Field(default=None, description="배포 시작 시각")
    ends_at: datetime | None = Field(default=None, description="마감 시각")
    target_type: TargetType = Field(default=TargetType.ALL, description="배포 대상 유형")
    target_ids: list[str] = Field(default_factory=list, description="대상 ID 목록")
    allow_multiple: bool = Field(default=False, description="중복 응답 허용")
    show_results: ShowResults = Field(default=ShowResults.AFTER_CLOSE, description="결과 공개 시점")
    template_id: str | None = Field(default=None, description="템플릿 참조")

    @model_validator(mode="after")
    def validate_dates(self) -> SurveyCreate:
        """마감 시각은 시작 시각 이후여야 한다."""
        if self.starts_at and self.ends_at and self.ends_at <= self.starts_at:
            msg = "마감 시각은 시작 시각 이후여야 합니다"
            raise ValueError(msg)
        return self


class SurveyUpdate(BaseModel):
    """설문 수정 요청 스키마."""

    title: str | None = None
    description: str | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    target_type: TargetType | None = None
    target_ids: list[str] | None = None
    allow_multiple: bool | None = None
    show_results: ShowResults | None = None


class Survey(BaseDocument):
    """설문 문서.

    설문/투표의 최상위 엔티티.
    """

    title: str = ""
    description: str = ""
    survey_type: SurveyType = SurveyType.SURVEY
    anonymity: Anonymity = Anonymity.NAMED
    status: SurveyStatus = SurveyStatus.DRAFT
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    target_type: TargetType = TargetType.ALL
    target_ids: list[str] = Field(default_factory=list)
    allow_multiple: bool = False
    show_results: ShowResults = ShowResults.AFTER_CLOSE
    response_count: int = 0
    template_id: str | None = None
