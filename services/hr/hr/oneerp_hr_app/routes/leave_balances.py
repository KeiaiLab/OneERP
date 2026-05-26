"""휴가잔액(LeaveBalance) 워크벤치 라우터."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from pydantic import BaseModel

from oneerp_hr_app.models.employee import EmployeeStatus
from oneerp_hr_app.models.leave import LeaveStatus
from oneerp_hr_app.models.leave_balance import LeaveBalance, LeaveBalanceCreate, LeaveBalanceUpdate

router = APIRouter(prefix="/api/v1/leave-balances", tags=["휴가잔액"])

_COLLECTION = "leave_balances"
_EMPLOYEE_COLLECTION = "employees"
_LEAVE_TYPE_COLLECTION = "leave_types"
_LEAVE_POLICY_COLLECTION = "leave_policies"
_LEAVE_APPLICATION_COLLECTION = "leave_applications"
_PREFIX = "LB"
_NOT_FOUND_MESSAGE = "휴가잔액을 찾을 수 없습니다"
_EXPIRY_SOON_DAYS = 60
_today_fn = date.today


class AnnualGrantRequest(BaseModel):
    """연차 자동 부여 요청."""

    fiscal_year: str
    employee_ids: list[str] | None = None


class CarryForwardRequest(BaseModel):
    """휴가 이월 요청."""

    from_year: str
    to_year: str
    employee_ids: list[str] | None = None


def _get_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_employee_repo(tenant_id: str) -> Repository:
    return Repository(_EMPLOYEE_COLLECTION, tenant_id=tenant_id)


def _get_leave_type_repo(tenant_id: str) -> Repository:
    return Repository(_LEAVE_TYPE_COLLECTION, tenant_id=tenant_id)


def _get_leave_policy_repo(tenant_id: str) -> Repository:
    return Repository(_LEAVE_POLICY_COLLECTION, tenant_id=tenant_id)


def _get_leave_application_repo(tenant_id: str) -> Repository:
    return Repository(_LEAVE_APPLICATION_COLLECTION, tenant_id=tenant_id)


def _allocated_days(document: dict[str, Any]) -> float:
    return float(document.get("allocated_days", document.get("total_allocated", 0)))


def _used_days(document: dict[str, Any]) -> float:
    return float(document.get("used_days", document.get("total_used", 0)))


def _remaining_days(document: dict[str, Any]) -> float:
    if document.get("balance") is not None:
        return float(document.get("balance", 0))
    return _allocated_days(document) - _used_days(document)


def _normalize_balance_payload(
    payload: dict[str, Any], current: dict[str, Any] | None = None
) -> dict[str, Any]:
    current = current or {}
    allocated = float(
        payload.get(
            "total_allocated",
            payload.get(
                "allocated_days", current.get("total_allocated", current.get("allocated_days", 0))
            ),
        ),
    )
    used = float(
        payload.get(
            "total_used",
            payload.get("used_days", current.get("total_used", current.get("used_days", 0))),
        ),
    )
    balance = payload.get("balance")
    normalized = dict(payload)
    normalized["total_allocated"] = allocated
    normalized["allocated_days"] = allocated
    normalized["total_used"] = used
    normalized["used_days"] = used
    normalized["balance"] = float(balance) if balance is not None else allocated - used
    return normalized


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    payload = dict(document)
    if "_id" in payload:
        payload["_id"] = str(payload["_id"])
        payload["id"] = payload["_id"]
    payload["total_allocated"] = _allocated_days(payload)
    payload["allocated_days"] = _allocated_days(payload)
    payload["total_used"] = _used_days(payload)
    payload["used_days"] = _used_days(payload)
    payload["remaining"] = _remaining_days(payload)
    payload["balance"] = _remaining_days(payload)
    return payload


def _to_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _days_until(expiry_date: Any) -> int | None:
    parsed = _to_date(expiry_date)
    if parsed is None:
        return None
    return (parsed - _today_fn()).days


def _resolve_employee_name(tenant_id: str, employee_id: str) -> str:
    if not employee_id:
        return ""
    employee = _get_employee_repo(tenant_id).find_by_id(employee_id)
    if not employee:
        return ""
    return str(employee.get("employee_name", ""))


def _find_leave_type(tenant_id: str, leave_type_name: str) -> dict[str, Any] | None:
    if not leave_type_name:
        return None
    leave_types = _get_leave_type_repo(tenant_id).find_many(
        query={"leave_type_name": leave_type_name},
        limit=1,
    )
    return leave_types[0] if leave_types else None


def _find_leave_policy(tenant_id: str, leave_type_id: str) -> dict[str, Any] | None:
    if not leave_type_id:
        return None
    policies = _get_leave_policy_repo(tenant_id).find_many(
        query={"leave_type_id": leave_type_id},
        limit=1000,
    )
    active_policies = [
        policy for policy in policies if str(policy.get("status", "active")).lower() != "inactive"
    ]
    return active_policies[0] if active_policies else (policies[0] if policies else None)


def _find_leave_applications(
    tenant_id: str, employee_id: str, leave_type_name: str
) -> list[dict[str, Any]]:
    return _get_leave_application_repo(tenant_id).find_many(
        query={"employee_id": employee_id, "leave_type": leave_type_name},
        limit=1000,
        sort=[("created_at", -1)],
    )


def _build_balance_summary(tenant_id: str, balance: dict[str, Any]) -> dict[str, Any]:
    employee_id = str(balance.get("employee", ""))
    leave_type_name = str(balance.get("leave_type", ""))
    leave_type = _find_leave_type(tenant_id, leave_type_name)
    leave_policy = _find_leave_policy(
        tenant_id, str(leave_type.get("_id", "")) if leave_type else ""
    )
    applications = _find_leave_applications(tenant_id, employee_id, leave_type_name)
    remaining_days = _remaining_days(balance)
    allocated_days = _allocated_days(balance)
    used_days = _used_days(balance)
    carry_forward_cap_days = (
        float(leave_policy.get("max_carry_forward_days", 0)) if leave_policy else 0.0
    )
    expected_carry_forward_days = min(max(remaining_days, 0.0), carry_forward_cap_days)
    utilization_rate_pct = (
        round((used_days / allocated_days) * 100, 1) if allocated_days > 0 else 0.0
    )
    expires_in_days = _days_until(balance.get("expiry_date"))

    return {
        "allocated_days": allocated_days,
        "used_days": used_days,
        "remaining_days": remaining_days,
        "open_application_count": sum(
            1
            for document in applications
            if str(document.get("status", LeaveStatus.OPEN.value)).lower() == LeaveStatus.OPEN.value
        ),
        "approved_application_count": sum(
            1
            for document in applications
            if str(document.get("status", LeaveStatus.OPEN.value)).lower()
            == LeaveStatus.APPROVED.value
        ),
        "carry_forward_cap_days": carry_forward_cap_days,
        "expected_carry_forward_days": expected_carry_forward_days,
        "utilization_rate_pct": utilization_rate_pct,
        "expires_in_days": expires_in_days,
    }


def _status_badge(_balance: dict[str, Any], summary: dict[str, Any]) -> str:
    remaining_days = summary["remaining_days"]
    expires_in_days = summary["expires_in_days"]
    if remaining_days <= 0:
        return "balance_exhausted"
    if expires_in_days is not None and expires_in_days <= _EXPIRY_SOON_DAYS:
        return "expiring_soon"
    if summary["expected_carry_forward_days"] > 0:
        return "carry_forward_ready"
    return "healthy"


def _recommended_action(summary: dict[str, Any], status_badge: str) -> str:
    if status_badge == "balance_exhausted":
        return "grant_annual_leave"
    if status_badge == "expiring_soon":
        return "review_expiry"
    if summary["expected_carry_forward_days"] > 0:
        return "run_carry_forward"
    return "monitor_leave_usage"


def _available_actions(summary: dict[str, Any]) -> list[str]:
    actions = ["edit"]
    if summary["open_application_count"] > 0 or summary["approved_application_count"] > 0:
        actions.append("open_leave_applications")
    if summary["expected_carry_forward_days"] > 0:
        actions.append("run_carry_forward")
    actions.append("view_leave_report")
    return actions


def _serialize_balance(tenant_id: str, balance: dict[str, Any]) -> dict[str, Any]:
    payload = _with_public_id(balance)
    payload["employee_name"] = _resolve_employee_name(tenant_id, str(balance.get("employee", "")))
    summary = _build_balance_summary(tenant_id, balance)
    payload["summary"] = summary
    payload["status_badge"] = _status_badge(balance, summary)
    payload["recommended_action"] = _recommended_action(summary, payload["status_badge"])
    payload["available_actions"] = _available_actions(summary)
    return payload


def _build_workbench_summary(documents: list[dict[str, Any]]) -> dict[str, Any]:
    employee_ids = {
        str(document.get("employee", "")) for document in documents if document.get("employee")
    }
    return {
        "employee_count": len(employee_ids),
        "expiring_soon_count": sum(
            1
            for document in documents
            if document["summary"]["expires_in_days"] is not None
            and document["summary"]["expires_in_days"] <= _EXPIRY_SOON_DAYS
            and document["summary"]["remaining_days"] > 0
        ),
        "carry_forward_ready_count": sum(
            1 for document in documents if document["summary"]["expected_carry_forward_days"] > 0
        ),
        "exhausted_count": sum(
            1 for document in documents if document["summary"]["remaining_days"] <= 0
        ),
        "total_remaining_days": float(
            sum(document["summary"]["remaining_days"] for document in documents)
        ),
        "total_expected_carry_forward_days": float(
            sum(document["summary"]["expected_carry_forward_days"] for document in documents)
        ),
    }


def _resolve_employee_ids(tenant_id: str, employee_ids: list[str] | None) -> list[str]:
    if employee_ids:
        return employee_ids
    employee_repo = _get_employee_repo(tenant_id)
    employees = employee_repo.find_many({}, limit=1000, sort=[("employee_name", 1)])
    return [
        str(employee.get("_id", ""))
        for employee in employees
        if employee.get("status") != EmployeeStatus.LEFT
    ]


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("leave_balance:create"))]
)
def create_leave_balance(body: LeaveBalanceCreate, user: CurrentUserDep) -> dict[str, Any]:
    """휴가잔액을 수동 등록한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    payload = _normalize_balance_payload(body.model_dump())
    document = LeaveBalance(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **payload,
    )
    repo.insert(document)
    return _serialize_balance(user.tenant_id, {"_id": doc_id, **payload})


@router.get("", dependencies=[Depends(require_permission("leave_balance:read"))])
def list_leave_balances(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    employee_id: str | None = None,
    leave_type: str | None = None,
    fiscal_year: str | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """휴가잔액 목록과 운영 요약을 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if employee_id:
        query["employee"] = employee_id
    if leave_type:
        query["leave_type"] = leave_type
    if fiscal_year:
        query["fiscal_year"] = fiscal_year
    documents = repo.find_many(
        query, limit=1000, sort=[("expiry_date", 1), ("employee", 1), ("leave_type", 1)]
    )
    serialized = [_serialize_balance(user.tenant_id, document) for document in documents]
    if status_badge:
        serialized = [
            document for document in serialized if document.get("status_badge") == status_badge
        ]
    total = len(serialized)
    skip = (page - 1) * page_size
    paginated = serialized[skip : skip + page_size]
    return {
        "data": paginated,
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _build_workbench_summary(serialized),
    }


@router.get("/report", dependencies=[Depends(require_permission("leave_balance:read"))])
def get_leave_balance_report(
    user: CurrentUserDep,
    employee_id: str | None = None,
    leave_type: str | None = None,
    fiscal_year: str | None = None,
) -> dict[str, Any]:
    """직원별 휴가 잔여 리포트를 반환한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if employee_id:
        query["employee"] = employee_id
    if leave_type:
        query["leave_type"] = leave_type
    if fiscal_year:
        query["fiscal_year"] = fiscal_year
    documents = repo.find_many(query, limit=1000, sort=[("employee", 1), ("leave_type", 1)])
    data = [_with_public_id(document) for document in documents]
    summary = {
        "total_allocated": sum(item["total_allocated"] for item in data),
        "total_used": sum(item["total_used"] for item in data),
        "total_remaining": sum(item["remaining"] for item in data),
    }
    return {
        "data": data,
        "total": len(data),
        "employee_id": employee_id or "",
        "leave_type": leave_type or "",
        "fiscal_year": fiscal_year or "",
        "summary": summary,
    }


@router.post("/grant-annual", dependencies=[Depends(require_permission("leave_balance:write"))])
def grant_annual_leave_balances(
    body: AnnualGrantRequest,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """직원별 연차를 자동 부여한다."""
    from oneerp_hr_app.services.leave_service import LeaveService

    service = LeaveService(tenant_id=user.tenant_id)
    target_employee_ids = _resolve_employee_ids(user.tenant_id, body.employee_ids)
    results = [
        service.grant_annual_leave(employee_id, fiscal_year=body.fiscal_year)
        for employee_id in target_employee_ids
    ]
    return {
        "fiscal_year": body.fiscal_year,
        "processed_count": len(results),
        "results": results,
        "summary": {
            "total_allocated": sum(float(item.get("allocated_days", 0)) for item in results),
        },
    }


@router.post("/carry-forward", dependencies=[Depends(require_permission("leave_balance:write"))])
def carry_forward_leave_balances(
    body: CarryForwardRequest,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """직원별 휴가 잔여를 다음 연도로 이월한다."""
    from oneerp_hr_app.services.leave_service import LeaveService

    service = LeaveService(tenant_id=user.tenant_id)
    target_employee_ids = _resolve_employee_ids(user.tenant_id, body.employee_ids)
    results = [
        service.carry_forward_leave(employee_id, from_year=body.from_year, to_year=body.to_year)
        for employee_id in target_employee_ids
    ]
    return {
        "from_year": body.from_year,
        "to_year": body.to_year,
        "processed_count": len(results),
        "results": results,
        "summary": {
            "carried_forward": sum(float(item.get("carried_forward", 0)) for item in results),
            "expired": sum(float(item.get("expired", 0)) for item in results),
        },
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("leave_balance:read"))])
def get_leave_balance(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """휴가잔액 상세를 조회한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    return _serialize_balance(user.tenant_id, document)


@router.get("/{doc_id}/summary", dependencies=[Depends(require_permission("leave_balance:read"))])
def get_leave_balance_summary(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """휴가잔액 상세 요약을 조회한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    serialized = _serialize_balance(user.tenant_id, document)
    return {
        "id": serialized["id"],
        "employee": serialized.get("employee", ""),
        "employee_name": serialized.get("employee_name", ""),
        "leave_type": serialized.get("leave_type", ""),
        "fiscal_year": serialized.get("fiscal_year", ""),
        "summary": serialized["summary"],
        "status_badge": serialized["status_badge"],
        "recommended_action": serialized["recommended_action"],
        "available_actions": serialized["available_actions"],
        "carry_forward_summary": {
            "carry_forward_cap_days": serialized["summary"]["carry_forward_cap_days"],
            "expected_carry_forward_days": serialized["summary"]["expected_carry_forward_days"],
            "expires_in_days": serialized["summary"]["expires_in_days"],
            "utilization_rate_pct": serialized["summary"]["utilization_rate_pct"],
        },
    }


@router.put("/{doc_id}", dependencies=[Depends(require_permission("leave_balance:write"))])
def update_leave_balance(
    doc_id: str,
    body: LeaveBalanceUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """휴가잔액을 수정한다."""
    repo = _get_repo(user.tenant_id)
    current = repo.find_by_id(doc_id)
    if not current:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert current is not None
    payload = _normalize_balance_payload(body.model_dump(exclude_none=True), current=current)
    payload["updated_by"] = user.sub
    repo.update_by_id(doc_id, payload)
    return _serialize_balance(user.tenant_id, {**current, **payload})


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("leave_balance:delete"))]
)
def delete_leave_balance(doc_id: str, user: CurrentUserDep) -> None:
    """휴가잔액을 삭제한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    repo.delete_by_id(doc_id)
