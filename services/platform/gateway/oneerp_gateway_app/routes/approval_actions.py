"""결재이력(ApprovalAction) 라우트 — 감사 추적 워크벤치."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, time

from bson import ObjectId
from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from pydantic import BaseModel

from ..audit_hooks import emit as audit_emit
from ..models.approval_action import ApprovalAction, ApprovalActionCreate

router = APIRouter(prefix="/api/v1/approval-actions", tags=["결재이력"])
_COLLECTION = "approval_actions"
_PREFIX = "AA"
_ACTION_BADGES = {
    "approve": "approved",
    "reject": "rejected",
    "delegate": "delegated",
    "pre_approve": "pre_approved",
}
_REQUEST_STATUS_BADGES = {
    "pending": "pending_review",
    "submitted": "submitted_review",
    "approved": "approved",
    "rejected": "rejected",
    "cancelled": "cancelled",
}


def _get_repo(tenant_id: str = "") -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_request_repo(tenant_id: str = "") -> Repository:
    return Repository("approval_requests", tenant_id=tenant_id)


def _build_request_scope(
    request_repo: Repository,
    *,
    approval_request: str | None = None,
    document_type: str | None = None,
    document_id: str | None = None,
) -> list[str] | None:
    if approval_request:
        return [approval_request]
    if not document_type and not document_id:
        return None
    request_query: dict[str, str] = {}
    if document_type:
        request_query["document_type"] = document_type
    if document_id:
        request_query["document_id"] = document_id
    requests = request_repo.find_many(request_query, limit=1000)
    return [doc["_id"] for doc in requests if doc.get("_id")]


def _build_action_query(
    *,
    approval_request_ids: list[str] | None,
    actor: str | None,
    action_type: str | None,
    from_date: date | None,
    to_date: date | None,
) -> dict:
    query: dict = {}
    if approval_request_ids is not None:
        if not approval_request_ids:
            return {"approval_request": {"$in": []}}
        query["approval_request"] = {"$in": approval_request_ids}
    if actor:
        query["actor"] = actor
    if action_type:
        query["action_type"] = action_type
    if from_date or to_date:
        date_query: dict = {}
        if from_date:
            date_query["$gte"] = datetime.combine(from_date, time.min, tzinfo=UTC)
        if to_date:
            date_query["$lte"] = datetime.combine(to_date, time.max, tzinfo=UTC)
        query["action_date"] = date_query
    return query


def _action_timestamp(doc: dict) -> datetime:
    acted_at = doc.get("acted_at") or doc.get("created_at")
    if isinstance(acted_at, datetime):
        return acted_at
    return datetime.min.replace(tzinfo=UTC)


def _build_request_map(actions: list[dict], request_repo: Repository) -> dict[str, dict]:
    request_ids = {
        doc.get("approval_request", "") for doc in actions if doc.get("approval_request")
    }
    return {request_id: request_repo.find_by_id(request_id) or {} for request_id in request_ids}


def _find_action_by_id(repo: Repository, doc_id: str) -> dict | None:
    doc = repo.find_by_id(doc_id)
    if doc:
        return doc
    try:
        object_id = ObjectId(doc_id)
    except Exception:
        return None
    matches = repo.find_many(query={"_id": object_id}, limit=1)
    return matches[0] if matches else None


def _get_action_badge(action_type: str) -> str:
    return _ACTION_BADGES.get(action_type, action_type or "recorded")


def _get_request_status_badge(status: str) -> str:
    return _REQUEST_STATUS_BADGES.get(status, status or "unknown")


def _get_total_steps(request_doc: dict, action: dict) -> int:
    approval_lines = request_doc.get("approval_lines", []) if request_doc else []
    line_steps = [int(line.get("step", 0) or 0) for line in approval_lines]
    return max(
        [
            int(action.get("step", 0) or 0),
            int(request_doc.get("current_step", 0) or 0),
            *line_steps,
            1,
        ]
    )


def _build_available_actions(action: dict) -> list[str]:
    actions = ["open_request", "open_document", "open_audit_report"]
    if action.get("delegate_to"):
        actions.append("open_delegate_context")
    return actions


def _build_request_summary(action: dict, request_doc: dict) -> dict:
    return {
        "approval_request": action.get("approval_request", ""),
        "requester": request_doc.get("requester", ""),
        "current_status": request_doc.get("status", action.get("request_status", "")),
        "current_step": int(request_doc.get("current_step", action.get("step", 0)) or 0),
        "total_steps": _get_total_steps(request_doc, action),
        "document_type": action.get("document_type") or request_doc.get("document_type", ""),
        "document_id": action.get("document_id") or request_doc.get("document_id", ""),
    }


def _serialize_action(action: dict, request_doc: dict) -> dict:
    serialized = {
        **action,
        "_id": str(action.get("_id", "")),
        "document_type": action.get("document_type") or request_doc.get("document_type", ""),
        "document_id": action.get("document_id") or request_doc.get("document_id", ""),
    }
    serialized["action_badge"] = _get_action_badge(str(serialized.get("action_type", "")))
    serialized["request_status_badge"] = _get_request_status_badge(
        str(serialized.get("request_status", ""))
    )
    serialized["delegate_summary"] = {
        "has_delegate": bool(serialized.get("delegate_to")),
        "delegate_to": serialized.get("delegate_to", ""),
    }
    serialized["request_summary"] = _build_request_summary(serialized, request_doc)
    serialized["available_actions"] = _build_available_actions(serialized)
    return serialized


def _build_summary(actions: list[dict]) -> dict:
    action_counts = Counter(
        action.get("action_type", "") for action in actions if action.get("action_type")
    )
    actor_counts = Counter(action.get("actor", "") for action in actions if action.get("actor"))
    request_status_counts = Counter(
        action.get("request_status", "") for action in actions if action.get("request_status")
    )
    document_refs: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for action in actions:
        key = (
            action.get("approval_request", ""),
            action.get("document_type", ""),
            action.get("document_id", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        document_refs.append(
            {
                "approval_request": key[0],
                "document_type": key[1],
                "document_id": key[2],
            }
        )

    ordered = sorted(actions, key=_action_timestamp)
    return {
        "total_actions": len(actions),
        "approval_request_count": len(
            {
                action.get("approval_request", "")
                for action in actions
                if action.get("approval_request")
            }
        ),
        "action_counts": dict(action_counts),
        "actor_counts": dict(actor_counts),
        "request_status_counts": dict(request_status_counts),
        "documents": document_refs,
        "first_acted_at": ordered[0].get("acted_at") if ordered else None,
        "last_acted_at": ordered[-1].get("acted_at") if ordered else None,
    }


class _DispatchActionBody(BaseModel):
    approval_request_id: str
    tenant_id: str
    target_doctype: str | None = None
    target_doc_id: str | None = None
    approver: str | None = None


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("approval_action:create"))]
)
async def create_approval_action(body: ApprovalActionCreate, user: CurrentUserDep) -> dict:
    repo = _get_repo(user.tenant_id)
    request_repo = _get_request_repo(user.tenant_id)
    request_doc = request_repo.find_by_id(body.approval_request)
    if not request_doc:
        raise OneERPError(
            status_code=404,
            error="not_found",
            detail="결재 요청을 찾을 수 없습니다",
        )

    doc_id = generate_name(_PREFIX)
    payload = body.model_dump(exclude_none=True)
    acted_at = payload.get("acted_at") or datetime.now(tz=UTC)
    payload["acted_at"] = acted_at
    payload.setdefault("action_date", acted_at.date())
    payload.setdefault("step", request_doc.get("current_step", 0))
    payload.setdefault("request_status", request_doc.get("status", "pending"))
    payload.setdefault("document_type", request_doc.get("document_type", ""))
    payload.setdefault("document_id", request_doc.get("document_id", ""))
    doc = ApprovalAction(_id=doc_id, **payload)
    repo.insert(doc)
    audit_emit(
        actor=str(user.sub),
        action="gateway.submit",
        resource=f"approval_action/{doc_id}",
        tenant_id=user.tenant_id,
        details={
            "approval_request": body.approval_request,
            "action_type": payload.get("action_type", ""),
        },
    )
    return {"approval_action_id": doc_id, "message": "결재이력이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("approval_action:read"))])
async def list_approval_actions(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    approval_request: str | None = None,
    actor: str | None = None,
    action_type: str | None = None,
    document_type: str | None = None,
    document_id: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    repo = _get_repo(user.tenant_id)
    request_repo = _get_request_repo(user.tenant_id)
    request_scope = _build_request_scope(
        request_repo,
        approval_request=approval_request,
        document_type=document_type,
        document_id=document_id,
    )
    query = _build_action_query(
        approval_request_ids=request_scope,
        actor=actor,
        action_type=action_type,
        from_date=from_date,
        to_date=to_date,
    )
    total = repo.count(query)
    records = repo.find_many(
        query,
        skip=0,
        limit=max(total, page_size, 1),
        sort=[("created_at", -1)],
    )
    request_map = _build_request_map(records, request_repo)
    serialized = [
        _serialize_action(action, request_map.get(action.get("approval_request", ""), {}))
        for action in records
    ]
    ordered = sorted(serialized, key=_action_timestamp, reverse=True)
    skip = (page - 1) * page_size
    return {
        "data": ordered[skip : skip + page_size],
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _build_summary(ordered),
    }


@router.get("/report", dependencies=[Depends(require_permission("approval_action:read"))])
async def report_approval_actions(
    user: CurrentUserDep,
    approval_request: str | None = None,
    actor: str | None = None,
    action_type: str | None = None,
    document_type: str | None = None,
    document_id: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> dict:
    repo = _get_repo(user.tenant_id)
    request_repo = _get_request_repo(user.tenant_id)
    request_scope = _build_request_scope(
        request_repo,
        approval_request=approval_request,
        document_type=document_type,
        document_id=document_id,
    )
    query = _build_action_query(
        approval_request_ids=request_scope,
        actor=actor,
        action_type=action_type,
        from_date=from_date,
        to_date=to_date,
    )
    timeline = repo.find_many(
        query,
        skip=0,
        limit=max(repo.count(query), 1),
        sort=[("created_at", 1)],
    )
    request_map = _build_request_map(timeline, request_repo)
    serialized_timeline = [
        _serialize_action(action, request_map.get(action.get("approval_request", ""), {}))
        for action in timeline
    ]
    serialized_timeline = sorted(serialized_timeline, key=_action_timestamp)
    return {
        "timeline": serialized_timeline,
        "summary": _build_summary(serialized_timeline),
    }


@router.post("/dispatch")
async def dispatch_approval_action(body: _DispatchActionBody) -> dict:
    """승인 완료 후속 액션을 감사 이력으로 기록한다."""
    request_repo = _get_request_repo(body.tenant_id)
    request_doc = request_repo.find_by_id(body.approval_request_id)
    if not request_doc:
        raise OneERPError(status_code=404, error="not_found", detail="결재 요청을 찾을 수 없습니다")

    repo = _get_repo(body.tenant_id)
    doc_id = generate_name(_PREFIX)
    acted_at = datetime.now(tz=UTC)
    doc = ApprovalAction(
        _id=doc_id,
        tenant_id=body.tenant_id,
        approval_request=body.approval_request_id,
        action_type="approve",
        actor=body.approver or "system:event",
        comment=(
            f"승인 후속 액션 디스패치: "
            f"{body.target_doctype or request_doc.get('document_type', '')}/"
            f"{body.target_doc_id or request_doc.get('document_id', '')}"
        ),
        acted_at=acted_at,
        action_date=acted_at.date(),
        step=int(request_doc.get("current_step", 0) or 0),
        request_status=str(request_doc.get("status", "approved") or "approved"),
        document_type=body.target_doctype or str(request_doc.get("document_type", "") or ""),
        document_id=body.target_doc_id or str(request_doc.get("document_id", "") or ""),
    )
    repo.insert(doc)
    return {
        "approval_action_id": doc_id,
        "message": "결재 승인 후속 액션이 기록되었습니다",
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("approval_action:read"))])
async def get_approval_action(doc_id: str, user: CurrentUserDep) -> dict:
    repo = _get_repo(user.tenant_id)
    request_repo = _get_request_repo(user.tenant_id)
    doc = _find_action_by_id(repo, doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="결재이력을 찾을 수 없습니다")

    request_doc = request_repo.find_by_id(doc.get("approval_request", "")) or {}
    related_actions = repo.find_many(
        {"approval_request": doc.get("approval_request", "")},
        skip=0,
        limit=max(repo.count({"approval_request": doc.get("approval_request", "")}), 1),
        sort=[("created_at", 1)],
    )
    serialized_doc = _serialize_action(doc, request_doc)
    serialized_doc["timeline_summary"] = _build_summary(
        [_serialize_action(action, request_doc) for action in related_actions]
    )
    return serialized_doc
