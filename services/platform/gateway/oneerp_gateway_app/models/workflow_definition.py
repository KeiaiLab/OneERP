"""워크플로우정의(WorkflowDefinition) 문서 모델 — Setup 모듈."""

from __future__ import annotations

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class WorkflowDefinitionCreate(BaseModel):
    """워크플로우정의 생성 요청 스키마."""

    workflow_name: str
    document_type: str = ""
    states: str = ""
    transitions: str = ""
    is_active: bool = True


class WorkflowDefinitionUpdate(BaseModel):
    """워크플로우정의 수정 요청 스키마."""

    workflow_name: str | None = None
    document_type: str | None = None
    states: str | None = None
    transitions: str | None = None
    is_active: bool | None = None


class WorkflowDefinition(BaseDocument):
    """워크플로우정의 문서 — Setup 워크플로우 정의 마스터.

    naming prefix: WFDF
    """

    workflow_name: str = ""
    document_type: str = ""
    states: str = ""
    transitions: str = ""
    is_active: bool = True
