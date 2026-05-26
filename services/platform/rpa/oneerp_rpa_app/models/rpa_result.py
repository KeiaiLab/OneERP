"""RPA 결과 모델 — 자동화 작업의 개별 단계 결과를 기록한다."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class RPAResultCreate(BaseModel):
    """RPA 결과 생성 요청 스키마."""

    task_id: str
    step_name: str
    success: bool = True
    data: dict = {}
    screenshot_url: str = ""
    duration_ms: int = 0
    error: str = ""


class RPAResultUpdate(BaseModel):
    """RPA 결과 수정 요청 스키마."""

    success: bool | None = None
    data: dict | None = None
    error: str | None = None


class RPAResult(BaseDocument):
    """RPA 결과 문서 — 작업 실행의 개별 단계를 기록한다."""

    task_id: str = ""
    step_name: str = ""
    success: bool = True
    data: dict = {}
    screenshot_url: str = ""
    duration_ms: int = 0
    error: str = ""
