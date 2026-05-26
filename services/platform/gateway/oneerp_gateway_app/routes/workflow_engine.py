"""워크플로우 엔진 라우트 — 상태 전이 실행 및 액션 조회.

core의 WorkflowService를 활용하여 문서의 워크플로우 상태를 관리한다.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from oneerp_core.workflow import WorkflowError, WorkflowService
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/workflow", tags=["워크플로우엔진"])

_RULE_COLLECTION = "workflow_rules"


class ApplyTransitionRequest(BaseModel):
    """상태 전이 요청 스키마."""

    target_state: str
    """전이할 목표 상태."""


class TransitionResultResponse(BaseModel):
    """상태 전이 응답 스키마."""

    success: bool
    from_state: str
    to_state: str
    transition_name: str


class ActionOption(BaseModel):
    """가능한 액션 옵션 스키마."""

    name: str
    to_state: str


def _get_workflow_service(tenant_id: str, document_type: str) -> WorkflowService:
    """테넌트와 문서 유형에 맞는 WorkflowService를 생성한다.

    워크플로우 규칙 저장소와 대상 문서 컬렉션 저장소를 주입한다.
    문서 컬렉션명은 document_type을 복수형(소문자 + 's')으로 변환하여 사용한다.
    """
    rule_repo = Repository(_RULE_COLLECTION, tenant_id=tenant_id)
    # 문서 유형을 컬렉션명으로 변환 (예: purchase_order → purchase_orders)
    doc_collection = f"{document_type}s"
    document_repo = Repository(doc_collection, tenant_id=tenant_id)
    return WorkflowService(rule_repo=rule_repo, document_repo=document_repo)


@router.post(
    "/{doc_type}/{doc_id}/apply",
    dependencies=[Depends(require_permission("workflow:execute"))],
)
async def apply_transition(
    doc_type: str,
    doc_id: str,
    body: ApplyTransitionRequest,
    user: CurrentUserDep,
) -> TransitionResultResponse:
    """문서의 워크플로우 상태 전이를 실행한다."""
    service = _get_workflow_service(user.tenant_id, doc_type)
    try:
        result = service.apply_transition(
            document_type=doc_type,
            doc_id=doc_id,
            target_state=body.target_state,
            user_roles=user.roles,
            user_id=user.sub,
        )
    except WorkflowError as e:
        raise OneERPError(
            status_code=400,
            error="workflow_error",
            detail=str(e),
        ) from e
    return TransitionResultResponse(
        success=result.success,
        from_state=result.from_state,
        to_state=result.to_state,
        transition_name=result.transition_name,
    )


@router.get(
    "/{doc_type}/{doc_id}/actions",
    dependencies=[Depends(require_permission("workflow:read"))],
)
async def get_available_actions(
    doc_type: str,
    doc_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """현재 문서 상태에서 사용자가 수행 가능한 액션 목록을 조회한다."""
    service = _get_workflow_service(user.tenant_id, doc_type)
    try:
        options = service.get_available_actions(
            document_type=doc_type,
            doc_id=doc_id,
            user_roles=user.roles,
        )
    except WorkflowError as e:
        raise OneERPError(
            status_code=400,
            error="workflow_error",
            detail=str(e),
        ) from e
    return {
        "doc_id": doc_id,
        "doc_type": doc_type,
        "actions": [
            ActionOption(name=opt.name, to_state=opt.to_state).model_dump() for opt in options
        ],
    }
