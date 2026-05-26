"""자동화 스케줄(AutomationSchedule) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AutomationScheduleCreate(BaseModel):
    """자동화 스케줄 생성 요청 스키마."""

    automation_definition_id: str
    cron_expression: str = ""
    is_active: bool = False


class AutomationScheduleUpdate(BaseModel):
    """자동화 스케줄 수정 요청 스키마."""

    automation_definition_id: str | None = None
    cron_expression: str | None = None
    is_active: bool | None = None


class AutomationSchedule(BaseDocument):
    """자동화 스케줄 문서."""

    automation_definition_id: str = ""
    cron_expression: str = ""
    is_active: bool = False
