"""휴먼 태스크(HumanTask) 문서 모델."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class HumanTaskCreate(BaseModel):
    """휴먼 태스크 생성 요청 스키마."""

    automation_run_id: str
    title: str = ""
    assignee: str = ""
    status: str = "open"


class HumanTaskUpdate(BaseModel):
    """휴먼 태스크 수정 요청 스키마."""

    automation_run_id: str | None = None
    title: str | None = None
    assignee: str | None = None
    status: str | None = None


class HumanTask(BaseDocument):
    """휴먼 태스크 문서."""

    automation_run_id: str = ""
    title: str = ""
    assignee: str = ""
    status: str = "open"
