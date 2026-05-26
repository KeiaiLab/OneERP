"""결재요청(ApprovalRequest) CRUD + 결재 액션 라우트.

CRUD 엔드포인트는 기존 패턴을 유지하고,
결재 액션(승인/거절/위임/전결/취소)은 ApprovalService를 경유한다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from pydantic import BaseModel

from ..audit_hooks import emit as audit_emit
from ..models.approval_request import (
    ApprovalRequest,
    ApprovalRequestCreate,
    ApprovalRequestUpdate,
)
from ..services.approval_service import ApprovalService

router = APIRouter(prefix="/api/v1/approval-requests", tags=["결재요청"])
_COLLECTION = "approval_requests"
_PREFIX = "AR"


def _get_repo(tenant_id: str = "") -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_current_pending_lines(doc: dict) -> list[dict]:
    """현재 단계의 pending 결재 라인을 반환한다."""
    current_step = doc.get("current_step", 1)
    return [
        line
        for line in doc.get("approval_lines", [])
        if line.get("step") == current_step and line.get("status", "pending") == "pending"
    ]


def _get_status_badge(doc: dict) -> str:
    """대기함/상세 화면용 상태 배지를 계산한다."""
    status = doc.get("status", "pending")
    if status in {"approved", "rejected", "cancelled"}:
        return status
    current_lines = _get_current_pending_lines(doc)
    if (
        any(line.get("approval_type") == "consensus" for line in current_lines)
        or len(current_lines) > 1
    ):
        return "consensus_pending"
    return "pending_approval"


def _build_available_actions(
    doc: dict,
    *,
    user_sub: str,
    user_roles: tuple[str, ...] | list[str],
) -> list[str]:
    """현재 사용자 기준으로 가능한 결재 액션을 계산한다."""
    if doc.get("status") not in {"pending", "submitted"}:
        return []

    roles = set(user_roles)
    actions: list[str] = []
    current_lines = _get_current_pending_lines(doc)
    matching_lines = [line for line in current_lines if line.get("approver") == user_sub]
    if matching_lines:
        actions.extend(["approve", "reject", "delegate"])
        if any(roles.intersection(line.get("pre_approval_roles", [])) for line in matching_lines):
            actions.append("pre_approve")
    if doc.get("requester") == user_sub:
        actions.append("cancel")
    return actions


def _serialize_approval_request(
    doc: dict,
    *,
    user_sub: str,
    user_roles: tuple[str, ...] | list[str],
) -> dict:
    """결재 대기함 UX에 필요한 파생 필드를 포함해 직렬화한다."""
    current_lines = _get_current_pending_lines(doc)
    approver_roles: list[str] = []
    for line in current_lines:
        role = str(line.get("approver_role", "") or "")
        if role and role not in approver_roles:
            approver_roles.append(role)

    serialized = dict(doc)
    serialized["total_steps"] = max(
        [
            serialized.get("current_step", 1),
            *[line.get("step", 0) for line in serialized.get("approval_lines", [])],
        ],
    )
    serialized["status_badge"] = _get_status_badge(serialized)
    serialized["waiting_on_me"] = any(line.get("approver") == user_sub for line in current_lines)
    serialized["current_approver_ids"] = [line.get("approver", "") for line in current_lines]
    serialized["current_approver_roles"] = approver_roles
    serialized["current_step_summary"] = {
        "step": serialized.get("current_step", 1),
        "approval_type": (
            "consensus"
            if any(line.get("approval_type") == "consensus" for line in current_lines)
            or len(current_lines) > 1
            else "single"
        ),
        "pending_approver_count": len(current_lines),
        "approvers": [
            {
                "approver": line.get("approver", ""),
                "approver_role": line.get("approver_role", ""),
                "status": line.get("status", "pending"),
                "is_current_user": line.get("approver") == user_sub,
                "can_pre_approve": bool(
                    line.get("approver") == user_sub
                    and set(user_roles).intersection(line.get("pre_approval_roles", []))
                ),
            }
            for line in current_lines
        ],
    }
    serialized["available_actions"] = _build_available_actions(
        serialized,
        user_sub=user_sub,
        user_roles=user_roles,
    )
    return serialized


def _build_request_summary(docs: list[dict], *, user_sub: str) -> dict:
    """결재 대기함 상단 요약을 계산한다."""
    by_status = dict.fromkeys(("pending", "submitted", "approved", "rejected", "cancelled"), 0)
    for doc in docs:
        status = doc.get("status", "pending")
        by_status[status] = by_status.get(status, 0) + 1

    return {
        "by_status": by_status,
        "waiting_on_me_count": sum(1 for doc in docs if doc.get("waiting_on_me")),
        "my_requested_count": sum(1 for doc in docs if doc.get("requester") == user_sub),
        "consensus_pending_count": sum(
            1 for doc in docs if doc.get("status_badge") == "consensus_pending"
        ),
    }


# -- 요청 스키마 --


class ApproveBody(BaseModel):
    """승인 요청 바디."""

    comment: str = ""


class RejectBody(BaseModel):
    """거절 요청 바디."""

    reason: str = ""
    comment: str = ""


class DelegateBody(BaseModel):
    """위임 요청 바디."""

    delegate_to: str


class PreApproveBody(BaseModel):
    """전결 요청 바디."""

    comment: str = ""


# -- CRUD --


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("approval_request:create"))]
)
async def create_approval_request(body: ApprovalRequestCreate, user: CurrentUserDep) -> dict:
    """결재요청을 생성한다."""
    if not body.approval_lines:
        service = ApprovalService(tenant_id=user.tenant_id)
        return service.create_request(
            document_type=body.document_type,
            document_id=body.document_id,
            requester=body.requester,
        )
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    doc = ApprovalRequest(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    audit_emit(
        actor=str(user.sub),
        action="gateway.create",
        resource=f"approval_request/{doc_id}",
        tenant_id=user.tenant_id,
        details={"document_type": body.document_type, "document_id": body.document_id},
    )
    return {"approval_request_id": doc_id, "message": "결재요청이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("approval_request:read"))])
async def list_approval_requests(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    requester: str | None = None,
    current_approver: str | None = None,
    current_approver_role: str | None = None,
    reference_doctype: str | None = None,
    reference_name: str | None = None,
) -> dict:
    """결재요청 목록을 페이지네이션으로 조회한다.

    필터:
        reference_doctype: 원본 문서 유형 (document_type 매핑)
        reference_name: 원본 문서 ID (document_id 매핑)
    """
    repo = _get_repo(user.tenant_id)
    query: dict = {}
    if status:
        query["status"] = status
    if requester:
        query["requester"] = requester
    if reference_doctype:
        query["document_type"] = reference_doctype
    if reference_name:
        query["document_id"] = reference_name
    skip = (page - 1) * page_size
    total_candidates = max(repo.count(query), page_size)
    candidates = repo.find_many(
        query,
        skip=0,
        limit=total_candidates,
        sort=[("created_at", -1)],
    )
    if current_approver or current_approver_role:
        matched_docs = [
            doc
            for doc in candidates
            if any(
                line.get("step") == doc.get("current_step", 1)
                and line.get("status", "pending") == "pending"
                and (not current_approver or line.get("approver") == current_approver)
                and (
                    not current_approver_role or line.get("approver_role") == current_approver_role
                )
                for line in doc.get("approval_lines", [])
            )
        ]
    else:
        matched_docs = candidates
    serialized_docs = [
        _serialize_approval_request(doc, user_sub=user.sub, user_roles=user.roles or ())
        for doc in matched_docs
    ]
    total = len(serialized_docs)
    data = serialized_docs[skip : skip + page_size]
    return {
        "data": data,
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _build_request_summary(serialized_docs, user_sub=user.sub),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("approval_request:read"))])
async def get_approval_request(doc_id: str, user: CurrentUserDep) -> dict:
    """결재요청 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="결재요청을 찾을 수 없습니다")
    return _serialize_approval_request(doc, user_sub=user.sub, user_roles=user.roles or ())


@router.put("/{doc_id}", dependencies=[Depends(require_permission("approval_request:write"))])
async def update_approval_request(
    doc_id: str, body: ApprovalRequestUpdate, user: CurrentUserDep
) -> dict:
    """결재요청을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="결재요청을 찾을 수 없습니다")
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "결재요청이 수정되었습니다"}


# -- 결재 액션 (ApprovalService 경유) --


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("approval_request:submit"))]
)
async def submit_approval_request(doc_id: str, user: CurrentUserDep) -> dict:
    """결재요청을 제출한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="결재요청을 찾을 수 없습니다")
    current_status = doc.get("status", "pending")
    if current_status != "pending":
        raise OneERPError(
            status_code=400,
            error="invalid_status",
            detail="대기 상태의 결재요청만 제출할 수 있습니다",
        )
    repo.update_by_id(doc_id, {"status": "submitted"})
    audit_emit(
        actor=str(user.sub),
        action="gateway.submit",
        resource=f"approval_request/{doc_id}",
        tenant_id=user.tenant_id,
        details={"status": "submitted"},
    )
    return {"message": "결재요청이 제출되었습니다"}


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("approval_request:cancel"))]
)
async def cancel_approval_request(doc_id: str, user: CurrentUserDep) -> dict:
    """결재요청을 취소한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="결재요청을 찾을 수 없습니다")
    # BR-APPR-015: 결재 취소는 기안자 본인만 가능
    requester = doc.get("requester", "")
    if requester != user.sub:
        raise OneERPError(
            status_code=403,
            error="forbidden",
            detail="결재 취소는 기안자 본인만 가능합니다",
        )
    current_status = doc.get("status", "pending")
    if current_status not in ("pending", "submitted"):
        raise OneERPError(
            status_code=400,
            error="invalid_status",
            detail="대기 또는 제출 상태의 결재요청만 취소할 수 있습니다",
        )
    repo.update_by_id(doc_id, {"status": "cancelled"})
    audit_emit(
        actor=str(user.sub),
        action="gateway.cancel",
        resource=f"approval_request/{doc_id}",
        tenant_id=user.tenant_id,
        details={"status": "cancelled"},
    )
    return {"message": "결재요청이 취소되었습니다"}


@router.post(
    "/{doc_id}/approve", dependencies=[Depends(require_permission("approval_request:write"))]
)
async def approve_request(doc_id: str, body: ApproveBody, user: CurrentUserDep) -> dict:
    """현재 단계를 승인한다.

    합의 결재 단계에서는 동일 단계의 모든 결재자가 승인해야 다음 단계로 진행.
    """
    service = ApprovalService(tenant_id=user.tenant_id)
    try:
        return service.approve(
            request_id=doc_id,
            approver=user.sub,
            comment=body.comment,
        )
    except ValueError as e:
        raise OneERPError(status_code=400, error="approval_error", detail=str(e)) from e


@router.post(
    "/{doc_id}/reject", dependencies=[Depends(require_permission("approval_request:write"))]
)
async def reject_request(doc_id: str, body: RejectBody, user: CurrentUserDep) -> dict:
    """결재를 거절한다.

    합의 결재 단계라도 한 명이 거절하면 전체 요청이 거절된다.
    """
    service = ApprovalService(tenant_id=user.tenant_id)
    try:
        # reason 우선, 없으면 comment 사용
        reject_reason = body.reason or body.comment
        return service.reject(
            request_id=doc_id,
            approver=user.sub,
            reason=reject_reason,
        )
    except ValueError as e:
        raise OneERPError(status_code=400, error="approval_error", detail=str(e)) from e


@router.post(
    "/{doc_id}/delegate", dependencies=[Depends(require_permission("approval_request:write"))]
)
async def delegate_request(doc_id: str, body: DelegateBody, user: CurrentUserDep) -> dict:
    """결재를 위임(대결)한다.

    활성 위임 규칙이 존재해야 한다.
    """
    service = ApprovalService(tenant_id=user.tenant_id)
    try:
        return service.delegate(
            request_id=doc_id,
            delegator=user.sub,
            delegate_to=body.delegate_to,
        )
    except ValueError as e:
        raise OneERPError(status_code=400, error="delegation_error", detail=str(e)) from e


@router.post(
    "/{doc_id}/pre-approve", dependencies=[Depends(require_permission("approval_request:write"))]
)
async def pre_approve_request(doc_id: str, body: PreApproveBody, user: CurrentUserDep) -> dict:
    """전결 — 상위 결재권자가 이후 단계를 건너뛰고 최종 승인한다.

    현재 단계에 pre_approval_roles가 설정되어 있고,
    사용자 역할이 포함되어야 전결이 가능하다.
    """
    service = ApprovalService(tenant_id=user.tenant_id)
    user_roles = user.roles or ()
    try:
        return service.pre_approve(
            request_id=doc_id,
            approver=user.sub,
            approver_roles=user_roles,
            comment=body.comment,
        )
    except ValueError as e:
        raise OneERPError(status_code=400, error="pre_approval_error", detail=str(e)) from e
