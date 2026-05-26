"""휴가유형(LeaveType) 워크벤치 라우터."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_conflict, raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_hr_app.models.leave import LeaveStatus
from oneerp_hr_app.models.leave_policy import LeavePolicyStatus
from oneerp_hr_app.models.leave_type import LeaveType, LeaveTypeCreate, LeaveTypeUpdate

router = APIRouter(prefix="/api/v1/leave-types", tags=["휴가유형"])

_COLLECTION = "leave_types"
_LEAVE_POLICY_COLLECTION = "leave_policies"
_LEAVE_BALANCE_COLLECTION = "leave_balances"
_LEAVE_APPLICATION_COLLECTION = "leave_applications"
_PREFIX = "LT"
_NOT_FOUND_MESSAGE = "휴가유형을 찾을 수 없습니다"


def _get_leave_type_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_leave_policy_repo(tenant_id: str) -> Repository:
    return Repository(_LEAVE_POLICY_COLLECTION, tenant_id=tenant_id)


def _get_leave_balance_repo(tenant_id: str) -> Repository:
    return Repository(_LEAVE_BALANCE_COLLECTION, tenant_id=tenant_id)


def _get_leave_application_repo(tenant_id: str) -> Repository:
    return Repository(_LEAVE_APPLICATION_COLLECTION, tenant_id=tenant_id)


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    payload = dict(document)
    if "_id" in payload:
        payload["id"] = payload["_id"]
    return payload


def _normalize_leave_type_name(name: str) -> str:
    return str(name).strip()


def _to_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _sort_leave_types(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        documents,
        key=lambda doc: (
            _normalize_leave_type_name(doc.get("leave_type_name", "")),
            str(doc.get("_id", "")),
        ),
    )


def _build_leave_type_summary(tenant_id: str, leave_type: dict[str, Any]) -> dict[str, Any]:
    leave_type_id = str(leave_type.get("_id", ""))
    leave_type_name = str(leave_type.get("leave_type_name", ""))
    policies = _get_leave_policy_repo(tenant_id).find_many(
        query={"leave_type_id": leave_type_id},
        limit=1000,
    )
    balances = _get_leave_balance_repo(tenant_id).find_many(
        query={"leave_type": leave_type_name},
        limit=1000,
    )
    applications = _get_leave_application_repo(tenant_id).find_many(
        query={"leave_type": leave_type_name},
        limit=1000,
    )

    open_application_count = sum(
        1
        for document in applications
        if str(document.get("status", LeaveStatus.OPEN.value)).lower() == LeaveStatus.OPEN.value
    )
    approved_application_count = sum(
        1
        for document in applications
        if str(document.get("status", LeaveStatus.OPEN.value)).lower() == LeaveStatus.APPROVED.value
    )
    active_policy_count = sum(
        1
        for document in policies
        if str(document.get("status", LeavePolicyStatus.ACTIVE.value)).lower()
        != LeavePolicyStatus.INACTIVE.value
    )
    max_carry_forward_days = max(
        (_to_decimal(document.get("max_carry_forward_days", 0)) for document in policies),
        default=Decimal(0),
    )
    total_allocated_days = sum(
        (_to_decimal(document.get("total_allocated", 0)) for document in balances), Decimal(0)
    )
    total_balance_days = sum(
        (_to_decimal(document.get("balance", 0)) for document in balances), Decimal(0)
    )

    return {
        "policy_count": len(policies),
        "active_policy_count": active_policy_count,
        "balance_employee_count": len(balances),
        "open_application_count": open_application_count,
        "approved_application_count": approved_application_count,
        "total_allocated_days": float(total_allocated_days),
        "total_balance_days": float(total_balance_days),
        "max_carry_forward_days": float(max_carry_forward_days),
    }


def _status_badge(leave_type: dict[str, Any], summary: dict[str, Any]) -> str:
    if summary["open_application_count"] > 0:
        return "request_backlog"
    if summary["policy_count"] == 0:
        return "policy_unassigned"
    if leave_type.get("is_paid", True) and leave_type.get("is_carry_forward", False):
        return "paid_carry_forward"
    if leave_type.get("is_carry_forward", False):
        return "unpaid_carry_forward"
    if leave_type.get("is_paid", True):
        return "paid_standard"
    return "unpaid_standard"


def _recommended_action(leave_type: dict[str, Any], summary: dict[str, Any]) -> str:
    if summary["open_application_count"] > 0:
        return "review_open_requests"
    if summary["policy_count"] == 0:
        return "assign_leave_policy"
    if leave_type.get("is_carry_forward", False):
        return "review_year_end_rollover"
    return "maintain_leave_type"


def _available_actions(leave_type: dict[str, Any], summary: dict[str, Any]) -> list[str]:
    actions = ["edit"]
    if summary["policy_count"] > 0:
        actions.append("open_leave_policies")
    else:
        actions.append("create_leave_policy")
    if summary["balance_employee_count"] > 0:
        actions.append("open_leave_balances")
    if summary["open_application_count"] > 0 or summary["approved_application_count"] > 0:
        actions.append("open_leave_applications")
    if leave_type.get("is_carry_forward", False):
        actions.append("review_carry_forward_policy")
    return actions


def _serialize_leave_type(tenant_id: str, leave_type: dict[str, Any]) -> dict[str, Any]:
    payload = _with_public_id(leave_type)
    summary = _build_leave_type_summary(tenant_id, leave_type)
    payload["summary"] = summary
    payload["status_badge"] = _status_badge(leave_type, summary)
    payload["recommended_action"] = _recommended_action(leave_type, summary)
    payload["available_actions"] = _available_actions(leave_type, summary)
    return payload


def _build_workbench_summary(documents: list[dict[str, Any]]) -> dict[str, Any]:
    total_balance_days = sum(
        (_to_decimal(document["summary"]["total_balance_days"]) for document in documents),
        Decimal(0),
    )
    return {
        "paid_type_count": sum(1 for document in documents if document.get("is_paid", True)),
        "carry_forward_type_count": sum(
            1 for document in documents if document.get("is_carry_forward", False)
        ),
        "request_backlog_count": sum(
            1 for document in documents if document.get("status_badge") == "request_backlog"
        ),
        "policy_unassigned_count": sum(
            1 for document in documents if document.get("status_badge") == "policy_unassigned"
        ),
        "total_balance_days": float(total_balance_days),
    }


def _ensure_unique_leave_type_name(
    repo: Repository,
    *,
    leave_type_name: str,
    current_leave_type_id: str | None = None,
) -> None:
    documents = repo.find_many(query={"leave_type_name": leave_type_name}, limit=1000)
    duplicates = [
        document
        for document in documents
        if str(document.get("_id", "")) != str(current_leave_type_id or "")
    ]
    if duplicates:
        raise_conflict("동일한 휴가유형명이 이미 존재합니다")


def _has_linked_usage(tenant_id: str, leave_type: dict[str, Any]) -> bool:
    leave_type_id = str(leave_type.get("_id", ""))
    leave_type_name = str(leave_type.get("leave_type_name", ""))
    return any(
        (
            _get_leave_policy_repo(tenant_id).count(query={"leave_type_id": leave_type_id}) > 0,
            _get_leave_balance_repo(tenant_id).count(query={"leave_type": leave_type_name}) > 0,
            _get_leave_application_repo(tenant_id).count(query={"leave_type": leave_type_name}) > 0,
        ),
    )


@router.post("", status_code=201, dependencies=[Depends(require_permission("leave_type:create"))])
def create_leave_type(body: LeaveTypeCreate, user: CurrentUserDep) -> dict[str, Any]:
    """휴가유형을 생성한다."""
    repo = _get_leave_type_repo(user.tenant_id)
    payload = body.model_dump(exclude_none=True)
    payload["leave_type_name"] = _normalize_leave_type_name(payload.get("leave_type_name", ""))
    if not payload["leave_type_name"]:
        raise_unprocessable("ERR-HR-051", "휴가유형명은 비워둘 수 없습니다")
    _ensure_unique_leave_type_name(repo, leave_type_name=payload["leave_type_name"])

    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    leave_type = LeaveType(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **payload,
    )
    repo.insert(leave_type)
    return _with_public_id({"_id": doc_id, **payload})


@router.get("", dependencies=[Depends(require_permission("leave_type:read"))])
def list_leave_types(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    *,
    is_paid: bool | None = None,
    is_carry_forward: bool | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """휴가유형 목록과 운영 요약을 조회한다."""
    repo = _get_leave_type_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if is_paid is not None:
        query["is_paid"] = is_paid
    if is_carry_forward is not None:
        query["is_carry_forward"] = is_carry_forward

    documents = [
        _serialize_leave_type(user.tenant_id, document)
        for document in _sort_leave_types(repo.find_many(query=query, limit=1000))
    ]
    if status_badge:
        documents = [
            document for document in documents if document.get("status_badge") == status_badge
        ]

    total = len(documents)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": documents[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _build_workbench_summary(documents),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("leave_type:read"))])
def get_leave_type(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """휴가유형 상세와 워크벤치 요약을 조회한다."""
    document = _get_leave_type_repo(user.tenant_id).find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    return _serialize_leave_type(user.tenant_id, document)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("leave_type:write"))])
def update_leave_type(doc_id: str, body: LeaveTypeUpdate, user: CurrentUserDep) -> dict[str, Any]:
    """휴가유형을 수정한다."""
    repo = _get_leave_type_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None

    update_data = body.model_dump(exclude_none=True)
    if "leave_type_name" in update_data:
        update_data["leave_type_name"] = _normalize_leave_type_name(
            update_data["leave_type_name"] or ""
        )
        if not update_data["leave_type_name"]:
            raise_unprocessable("ERR-HR-051", "휴가유형명은 비워둘 수 없습니다")
        _ensure_unique_leave_type_name(
            repo,
            leave_type_name=update_data["leave_type_name"],
            current_leave_type_id=doc_id,
        )
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return _serialize_leave_type(user.tenant_id, {**document, **update_data})


@router.get("/{doc_id}/summary", dependencies=[Depends(require_permission("leave_type:read"))])
def get_leave_type_summary(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """휴가유형 운영 카드 데이터를 반환한다."""
    document = _get_leave_type_repo(user.tenant_id).find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    summary = _build_leave_type_summary(user.tenant_id, document)
    return {
        "leave_type": _with_public_id(document),
        "summary": summary,
        "status_badge": _status_badge(document, summary),
        "recommended_action": _recommended_action(document, summary),
        "available_actions": _available_actions(document, summary),
    }


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("leave_type:delete"))]
)
def delete_leave_type(doc_id: str, user: CurrentUserDep) -> None:
    """정책·잔액·휴가신청 이력이 있는 휴가유형은 삭제하지 못하게 한다."""
    repo = _get_leave_type_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    if _has_linked_usage(user.tenant_id, document):
        raise_unprocessable(
            "ERR-HR-050", "휴가 정책/잔액/신청 이력이 있는 휴가유형은 삭제할 수 없습니다"
        )
    repo.delete_by_id(doc_id)
