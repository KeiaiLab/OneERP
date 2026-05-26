"""통합 플로우 모델 — 데이터 연동 파이프라인 정의를 관리한다."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class FlowStepConfig(BaseModel):
    """플로우 단계 설정."""

    step_order: int = 0
    step_type: str = "transform"  # extract/transform/load/validate/notify
    connector_id: str = ""
    mapping_id: str = ""
    config: dict = {}


class IntegrationFlowCreate(BaseModel):
    """통합 플로우 생성 요청 스키마."""

    flow_name: str
    flow_type: str = "etl"  # etl/sync/event/batch
    source_connector_id: str = ""
    target_connector_id: str = ""
    mapping_id: str = ""
    schedule: str = ""  # cron 표현식
    steps: list[dict] = []
    description: str = ""


class IntegrationFlowUpdate(BaseModel):
    """통합 플로우 수정 요청 스키마."""

    flow_name: str | None = None
    schedule: str | None = None
    steps: list[dict] | None = None
    is_active: bool | None = None
    description: str | None = None


class IntegrationFlow(BaseDocument):
    """통합 플로우 문서 — 데이터 연동 파이프라인 정의를 저장한다."""

    flow_name: str = ""
    flow_type: str = "etl"
    source_connector_id: str = ""
    target_connector_id: str = ""
    mapping_id: str = ""
    schedule: str = ""
    steps: list[dict] = []
    description: str = ""
    is_active: bool = True
    last_run_at: str = ""
    last_run_status: str = "never"  # never/success/failed/running
