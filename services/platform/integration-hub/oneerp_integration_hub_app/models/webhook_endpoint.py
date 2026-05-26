"""웹훅 엔드포인트 모델 — 외부 시스템 웹훅 수신 설정을 관리한다."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class WebhookEndpointCreate(BaseModel):
    """웹훅 엔드포인트 생성 요청 스키마."""

    endpoint_name: str
    source_system: str = ""
    event_types: list[str] = []
    secret_key: str = ""
    target_flow_id: str = ""
    description: str = ""


class WebhookEndpointUpdate(BaseModel):
    """웹훅 엔드포인트 수정 요청 스키마."""

    endpoint_name: str | None = None
    event_types: list[str] | None = None
    secret_key: str | None = None
    target_flow_id: str | None = None
    is_active: bool | None = None
    description: str | None = None


class WebhookEndpoint(BaseDocument):
    """웹훅 엔드포인트 문서 — 웹훅 수신 설정 정보를 저장한다."""

    endpoint_name: str = ""
    source_system: str = ""
    event_types: list[str] = []
    secret_key: str = ""
    target_flow_id: str = ""
    description: str = ""
    is_active: bool = True
    received_count: int = 0
    last_received_at: str = ""
