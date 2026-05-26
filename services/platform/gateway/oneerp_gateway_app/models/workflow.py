"""워크플로우 규칙(WorkflowRule) 모델 정의."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class WorkflowState(BaseModel):
    """워크플로우 상태 정의."""

    state_name: str
    allow_edit: bool = False
    doc_status: int = 0


class WorkflowTransition(BaseModel):
    """워크플로우 전환 규칙."""

    from_state: str
    to_state: str
    allowed_roles: list[str] = []


class WorkflowRule(BaseDocument):
    """워크플로우 규칙 문서 — 문서 워크플로우 정의.

    naming prefix: WF
    """

    document_type: str
    states: list[WorkflowState] = []
    transitions: list[WorkflowTransition] = []


class WorkflowRuleCreate(BaseModel):
    """워크플로우 규칙 생성 요청 스키마."""

    document_type: str
    states: list[WorkflowState] = []
    transitions: list[WorkflowTransition] = []


class WorkflowRuleUpdate(BaseModel):
    """워크플로우 규칙 수정 요청 스키마 — 모든 필드 선택적."""

    document_type: str | None = None
    states: list[WorkflowState] | None = None
    transitions: list[WorkflowTransition] | None = None
