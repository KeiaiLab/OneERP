"""자동화 트리거(AutomationTrigger) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AutomationTriggerCreate(BaseModel):
    """자동화 트리거 생성 요청 스키마."""

    automation_definition_id: str
    event_name: str = ""
    is_active: bool = False


class AutomationTriggerUpdate(BaseModel):
    """자동화 트리거 수정 요청 스키마."""

    automation_definition_id: str | None = None
    event_name: str | None = None
    is_active: bool | None = None


class AutomationTrigger(BaseDocument):
    """자동화 트리거 문서."""

    automation_definition_id: str = ""
    event_name: str = ""
    is_active: bool = False
