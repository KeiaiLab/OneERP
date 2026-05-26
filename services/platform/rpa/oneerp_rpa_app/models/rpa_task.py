"""RPA 작업 모델 — 자동화 작업의 생성·추적·결과를 관리한다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class RPATaskCreate(BaseModel):
    """RPA 작업 생성 요청 스키마."""

    task_type: (
        str  # hometax_issue, hometax_query, banking_transactions, banking_balance, insurance_status
    )
    input_data: dict = {}
    device_id: str = ""
    priority: int = 0  # 0=일반, 1=긴급


class RPATaskUpdate(BaseModel):
    """RPA 작업 수정 요청 스키마."""

    status: str | None = None
    input_data: dict | None = None
    device_id: str | None = None
    priority: int | None = None
    error_message: str | None = None


class RPATask(BaseDocument):
    """RPA 작업 문서 — 자동화 작업 상태와 결과를 저장한다."""

    task_type: str = ""
    status: str = "pending"  # pending/running/completed/failed
    input_data: dict = {}
    result_data: dict = {}
    screenshot_urls: list[str] = []
    error_message: str = ""
    device_id: str = ""
    priority: int = 0
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0
    max_retries: int = 3
