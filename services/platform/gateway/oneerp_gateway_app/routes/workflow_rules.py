"""워크플로우 규칙(WorkflowRule) CRUD 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.workflow import WorkflowRule, WorkflowRuleCreate, WorkflowRuleUpdate

router = APIRouter(prefix="/api/v1/workflow-rules", tags=["워크플로우"])

_COLLECTION = "workflow_rules"
_PREFIX = "WF"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("workflow_rule:create"))]
)
async def create_workflow_rule(body: WorkflowRuleCreate, user: CurrentUserDep) -> dict[str, Any]:
    """워크플로우 규칙을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    rule = WorkflowRule(
        _id=doc_id,
        tenant_id=user.tenant_id,
        document_type=body.document_type,
        states=body.states,
        transitions=body.transitions,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(rule)
    return {"id": doc_id, "message": "워크플로우 규칙이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("workflow_rule:read"))])
async def list_workflow_rules(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """워크플로우 규칙 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    docs = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = repo.count()
    return {
        "data": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("workflow_rule:read"))])
async def get_workflow_rule(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """워크플로우 규칙 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="워크플로우 규칙을 찾을 수 없습니다"
        )
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("workflow_rule:write"))])
async def update_workflow_rule(
    doc_id: str,
    body: WorkflowRuleUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """워크플로우 규칙을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="워크플로우 규칙을 찾을 수 없습니다"
        )

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="bad_request", detail="수정할 내용이 없습니다")
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "워크플로우 규칙이 수정되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("workflow_rule:delete"))]
)
async def delete_workflow_rule(doc_id: str, user: CurrentUserDep) -> None:
    """워크플로우 규칙을 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="워크플로우 규칙을 찾을 수 없습니다"
        )

    repo.delete_by_id(doc_id)
