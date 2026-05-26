"""자동화 실행(AutomationRun) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AutomationRunCreate(BaseModel):
    """자동화 실행 생성 요청 스키마."""

    automation_definition_id: str
    status: str = "draft"
    triggered_by: str = ""


class AutomationRunUpdate(BaseModel):
    """자동화 실행 수정 요청 스키마."""

    automation_definition_id: str | None = None
    status: str | None = None
    triggered_by: str | None = None


class AutomationRun(BaseDocument):
    """자동화 실행 문서."""

    automation_definition_id: str = ""
    status: str = "draft"
    triggered_by: str = ""
