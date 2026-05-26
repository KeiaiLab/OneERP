"""실행 큐 항목 모델."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QueueItem(BaseModel):
    """큐에 등록된 자동화 실행 항목."""

    run_id: str = Field(default="")
    automation_id: str
    version: int
    status: str = "queued"
    priority: str = "normal"
    input_params: dict = Field(default_factory=dict)
