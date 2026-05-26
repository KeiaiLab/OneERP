"""자동화 워크플로우 모델 — 마케팅 자동화 시나리오를 관리한다."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class WorkflowStepConfig(BaseModel):
    """워크플로우 단계 설정."""

    step_order: int = 0
    step_type: str = "send_email"  # send_email/wait/condition/send_sms/update_tag/webhook
    config: dict = {}
    delay_hours: int = 0


class AutomationWorkflowCreate(BaseModel):
    """자동화 워크플로우 생성 요청 스키마."""

    workflow_name: str
    trigger_type: str = "event"  # event/schedule/manual
    trigger_config: dict = {}
    steps: list[dict] = []
    description: str = ""


class AutomationWorkflowUpdate(BaseModel):
    """자동화 워크플로우 수정 요청 스키마."""

    workflow_name: str | None = None
    trigger_config: dict | None = None
    steps: list[dict] | None = None
    is_active: bool | None = None
    description: str | None = None


class AutomationWorkflow(BaseDocument):
    """자동화 워크플로우 문서 — 마케팅 자동화 시나리오를 저장한다."""

    workflow_name: str = ""
    trigger_type: str = "event"
    trigger_config: dict = {}
    steps: list[dict] = []
    description: str = ""
    is_active: bool = True
    enrolled_count: int = 0
    completed_count: int = 0
