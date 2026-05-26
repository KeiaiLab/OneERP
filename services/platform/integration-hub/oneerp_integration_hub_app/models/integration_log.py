"""통합 로그 모델 — 연동 실행 이력과 에러를 기록한다."""

from __future__ import annotations

from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import datetime


class IntegrationLogCreate(BaseModel):
    """통합 로그 생성 요청 스키마."""

    flow_id: str = ""
    connector_id: str = ""
    direction: str = "outbound"  # inbound/outbound
    status: str = "started"  # started/success/failed/partial
    request_payload: dict = {}
    response_payload: dict = {}
    records_processed: int = 0
    records_failed: int = 0
    error_message: str = ""


class IntegrationLogUpdate(BaseModel):
    """통합 로그 수정 요청 스키마."""

    status: str | None = None
    response_payload: dict | None = None
    records_processed: int | None = None
    records_failed: int | None = None
    error_message: str | None = None


class IntegrationLog(BaseDocument):
    """통합 로그 문서 — 연동 실행 이력을 저장한다."""

    flow_id: str = ""
    connector_id: str = ""
    direction: str = "outbound"
    status: str = "started"
    request_payload: dict = {}
    response_payload: dict = {}
    records_processed: int = 0
    records_failed: int = 0
    error_message: str = ""
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_ms: int = 0
