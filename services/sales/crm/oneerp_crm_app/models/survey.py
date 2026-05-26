"""설문조사(Survey) 문서 모델."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class SurveyCreate(BaseModel):
    """설문조사 생성 요청 스키마."""

    survey_name: str
    description: str = ""
    start_date: date | None = None
    end_date: date | None = None
    response_count: int = 0
    is_active: bool = True


class SurveyUpdate(BaseModel):
    """설문조사 수정 요청 스키마."""

    survey_name: str | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    response_count: int | None = None
    is_active: bool | None = None


class Survey(BaseDocument):
    """설문조사 문서."""

    survey_name: str = ""
    description: str = ""
    start_date: date | None = None
    end_date: date | None = None
    response_count: int = 0
    is_active: bool = True
