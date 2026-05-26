"""이슈(Issue) API 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request, raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_crm_app.models.issue import Issue, IssueCreate, IssueResolve, IssueStatus, IssueUpdate

router = APIRouter(prefix="/api/v1/issues", tags=["이슈"])

_COLLECTION = "issues"
_PREFIX = "ISS"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("issue:create"))])
def create_issue(body: IssueCreate, user: CurrentUserDep) -> dict[str, Any]:
    """이슈를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    issue = Issue(
        _id=doc_id,
        tenant_id=user.tenant_id,
        subject=body.subject,
        description=body.description,
        customer_id=body.customer_id,
        priority=body.priority,
        assigned_to=body.assigned_to,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(issue)
    return {"id": doc_id, "message": "이슈가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("issue:read"))])
def list_issues(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """이슈 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("issue:read"))])
def get_issue(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """이슈 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("이슈를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("issue:write"))])
def update_issue(
    doc_id: str,
    body: IssueUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """이슈를 수정한다. open 또는 in_progress 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("이슈를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    current_status = doc.get("status", IssueStatus.OPEN)
    if current_status in (IssueStatus.RESOLVED, IssueStatus.CLOSED):
        raise_bad_request("해결 또는 종료된 이슈는 수정할 수 없습니다")

    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "이슈가 수정되었습니다"}


@router.post("/{doc_id}/resolve", dependencies=[Depends(require_permission("issue:create"))])
def resolve_issue(
    doc_id: str,
    body: IssueResolve,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """이슈를 해결한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("이슈를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    current_status = doc.get("status", IssueStatus.OPEN)
    if current_status in (IssueStatus.RESOLVED, IssueStatus.CLOSED):
        raise_bad_request("이미 해결 또는 종료된 이슈입니다")

    repo.update_by_id(
        doc_id,
        {
            "status": IssueStatus.RESOLVED,
            "resolution": body.resolution,
            "updated_by": user.sub,
        },
    )
    return {"id": doc_id, "message": "이슈가 해결되었습니다"}


@router.post("/{doc_id}/close", dependencies=[Depends(require_permission("issue:create"))])
def close_issue(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """이슈를 종료한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("이슈를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    current_status = doc.get("status", IssueStatus.OPEN)
    if current_status == IssueStatus.CLOSED:
        raise_bad_request("이미 종료된 이슈입니다")
    if current_status != IssueStatus.RESOLVED:
        raise_unprocessable("ERR-CRM-010", "해결(resolved) 상태의 이슈만 종료할 수 있습니다")

    repo.update_by_id(
        doc_id,
        {
            "status": IssueStatus.CLOSED,
            "updated_by": user.sub,
        },
    )
    return {"id": doc_id, "message": "이슈가 종료되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("issue:delete"))]
)
def delete_issue(doc_id: str, user: CurrentUserDep) -> None:
    """이슈를 삭제한다. open 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("이슈를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    current_status = doc.get("status", IssueStatus.OPEN)
    if current_status != IssueStatus.OPEN:
        raise_bad_request("open 상태의 이슈만 삭제할 수 있습니다")

    repo.delete_by_id(doc_id)
