"""휴가신청(LeaveApplication) 워크벤치 라우터."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_hr_app.models.employee import EmployeeStatus
from oneerp_hr_app.models.leave import LeaveApplication, LeaveApplicationCreate, LeaveStatus
from oneerp_hr_app.services.leave_service import LeaveService

router = APIRouter(prefix="/api/v1/leave-applications", tags=["휴가신청"])

_COLLECTION = "leave_applications"
_LEAVE_TYPE_COLLECTION = "leave_types"
_EMPLOYEE_COLLECTION = "employees"
_LEAVE_BALANCE_COLLECTION = "leave_balances"
_PREFIX = "LA"
_NOT_FOUND_MESSAGE = "휴가 신청을 찾을 수 없습니다"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""

    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_leave_type_repo(tenant_id: str) -> Repository:
    """휴가 유형 검증용 Repository를 반환한다."""

    return Repository(_LEAVE_TYPE_COLLECTION, tenant_id=tenant_id)


def _get_employee_repo(tenant_id: str) -> Repository:
    """직원 검증용 Repository를 반환한다."""

    return Repository(_EMPLOYEE_COLLECTION, tenant_id=tenant_id)


def _get_leave_balance_repo(tenant_id: str) -> Repository:
    """휴가 잔액 조회용 Repository를 반환한다."""

    return Repository(_LEAVE_BALANCE_COLLECTION, tenant_id=tenant_id)


def _to_float(value: Any) -> float:
    if value in (None, ""):
        return 0.0
    return float(value)


def _stringify_date(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    payload = dict(document)
    if "_id" in payload:
        payload["_id"] = str(payload["_id"])
        payload["id"] = payload["_id"]
    payload["status"] = str(payload.get("status", LeaveStatus.OPEN.value)).lower()
    payload["from_date"] = _stringify_date(payload.get("from_date"))
    payload["to_date"] = _stringify_date(payload.get("to_date"))
    payload["total_days"] = _to_float(payload.get("total_days", 0))
    return payload


def _build_leave_balance_summary(tenant_id: str, document: dict[str, Any]) -> dict[str, Any]:
    employee_id = str(document.get("employee_id") or document.get("employee") or "")
    leave_type = str(document.get("leave_type") or "")
    allocated_days = 0.0
    used_days = 0.0
    remaining_days = 0.0
    if employee_id and leave_type:
        balances = _get_leave_balance_repo(tenant_id).find_many(
            query={"employee": employee_id, "leave_type": leave_type},
            limit=1,
        )
        if balances:
            balance = balances[0]
            allocated_days = _to_float(
                balance.get("allocated_days", balance.get("total_allocated", 0)),
            )
            used_days = _to_float(balance.get("used_days", balance.get("total_used", 0)))
            if balance.get("balance") is not None:
                remaining_days = _to_float(balance.get("balance"))
            else:
                remaining_days = allocated_days - used_days

    requested_days = _to_float(document.get("total_days", 0))
    remaining_after_request = remaining_days - requested_days
    return {
        "allocated_days": allocated_days,
        "used_days": used_days,
        "remaining_days": remaining_days,
        "requested_days": requested_days,
        "remaining_after_request": remaining_after_request,
        "has_sufficient_balance": remaining_after_request >= 0,
    }


def _build_period_summary(document: dict[str, Any]) -> dict[str, Any]:
    from_date = _stringify_date(document.get("from_date"))
    to_date = _stringify_date(document.get("to_date"))
    return {
        "from_date": from_date,
        "to_date": to_date,
        "total_days": _to_float(document.get("total_days", 0)),
        "is_single_day": bool(from_date and to_date and from_date == to_date),
    }


def _status_badge(document: dict[str, Any], leave_balance_summary: dict[str, Any]) -> str:
    status = str(document.get("status", LeaveStatus.OPEN.value)).lower()
    if status == LeaveStatus.APPROVED.value:
        return "approved_deducted"
    if status == LeaveStatus.REJECTED.value:
        return "rejected_closed"
    if leave_balance_summary["has_sufficient_balance"]:
        return "pending_approval"
    return "pending_balance_review"


def _recommended_action(document: dict[str, Any], leave_balance_summary: dict[str, Any]) -> str:
    status = str(document.get("status", LeaveStatus.OPEN.value)).lower()
    if status == LeaveStatus.APPROVED.value:
        return "review_attendance_sync"
    if status == LeaveStatus.REJECTED.value:
        return "review_rejection_reason"
    if leave_balance_summary["has_sufficient_balance"]:
        return "approve_or_reject"
    return "adjust_leave_balance"


def _available_actions(document: dict[str, Any]) -> list[str]:
    status = str(document.get("status", LeaveStatus.OPEN.value)).lower()
    if status == LeaveStatus.OPEN.value:
        return ["approve", "reject", "delete"]
    if status == LeaveStatus.APPROVED.value:
        return ["view_leave_balance", "review_attendance_sync"]
    return ["view_leave_balance"]


def _serialize_leave_application(tenant_id: str, document: dict[str, Any]) -> dict[str, Any]:
    payload = _with_public_id(document)
    leave_balance_summary = _build_leave_balance_summary(tenant_id, payload)
    period_summary = _build_period_summary(payload)
    payload["leave_balance_summary"] = leave_balance_summary
    payload["period_summary"] = period_summary
    payload["status_badge"] = _status_badge(payload, leave_balance_summary)
    payload["recommended_action"] = _recommended_action(payload, leave_balance_summary)
    payload["available_actions"] = _available_actions(payload)
    return payload


def _build_workbench_summary(documents: list[dict[str, Any]]) -> dict[str, Any]:
    open_documents = [
        document for document in documents if document.get("status") == LeaveStatus.OPEN.value
    ]
    approved_documents = [
        document for document in documents if document.get("status") == LeaveStatus.APPROVED.value
    ]
    rejected_documents = [
        document for document in documents if document.get("status") == LeaveStatus.REJECTED.value
    ]
    return {
        "open_count": len(open_documents),
        "approved_count": len(approved_documents),
        "rejected_count": len(rejected_documents),
        "pending_days": sum(
            _to_float(document.get("total_days", 0)) for document in open_documents
        ),
        "approved_days": sum(
            _to_float(document.get("total_days", 0)) for document in approved_documents
        ),
        "insufficient_balance_count": sum(
            1 for document in documents if document.get("status_badge") == "pending_balance_review"
        ),
        "employee_count": len(
            {
                str(document.get("employee_id") or document.get("employee") or "")
                for document in documents
                if document.get("employee_id") or document.get("employee")
            }
        ),
    }


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(require_permission("leave_application:create"))],
)
def create_leave_application(
    body: LeaveApplicationCreate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """휴가 신청을 생성한다."""

    repo = _get_repo(user.tenant_id)
    leave_type_repo = _get_leave_type_repo(user.tenant_id)
    employee_repo = _get_employee_repo(user.tenant_id)
    leave_types = leave_type_repo.find_many(query={"leave_type_name": body.leave_type}, limit=1)
    leave_type = leave_types[0] if leave_types else None
    if not leave_type or not leave_type.get("is_active", True):
        raise_unprocessable("ERR-HR-037", "사용할 수 없는 휴가 유형입니다")
    employee = employee_repo.find_by_id(body.employee_id)
    if not employee:
        raise_not_found("직원을 찾을 수 없습니다")
    assert employee is not None
    if employee.get("status") == EmployeeStatus.LEFT:
        raise_unprocessable("ERR-HR-038", "퇴사한 직원입니다")
    if body.from_date > body.to_date:
        raise_unprocessable("ERR-HR-035", "시작일이 종료일보다 클 수 없습니다")

    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    leave = LeaveApplication(
        _id=doc_id,
        tenant_id=user.tenant_id,
        employee_id=body.employee_id,
        employee_name=body.employee_name or employee.get("employee_name", ""),
        leave_type=body.leave_type,
        from_date=body.from_date,
        to_date=body.to_date,
        total_days=body.total_days,
        reason=body.reason,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(leave)
    return {"id": doc_id, "_id": doc_id, "message": "휴가 신청이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("leave_application:read"))])
def list_leave_applications(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    employee_id: str | None = None,
    leave_type: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """휴가 신청 목록과 운영 요약을 조회한다."""

    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if employee_id:
        query["employee_id"] = employee_id
    if leave_type:
        query["leave_type"] = leave_type
    if status:
        query["status"] = status.lower()

    documents = [
        _serialize_leave_application(user.tenant_id, document)
        for document in repo.find_many(query=query, limit=1000, sort=[("created_at", -1)])
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


@router.get(
    "/{doc_id}/summary",
    dependencies=[Depends(require_permission("leave_application:read"))],
)
def get_leave_application_summary(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """휴가 신청 워크벤치 요약을 반환한다."""

    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    return _serialize_leave_application(user.tenant_id, document)


@router.get("/{doc_id}", dependencies=[Depends(require_permission("leave_application:read"))])
def get_leave_application(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """휴가 신청 상세 정보를 조회한다."""

    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    return _serialize_leave_application(user.tenant_id, document)


@router.post(
    "/{doc_id}/approve",
    dependencies=[Depends(require_permission("leave_application:create"))],
)
def approve_leave_application(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """휴가 신청을 승인한다."""

    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    service = LeaveService(tenant_id=user.tenant_id)
    service.process_leave_application(doc_id, action="approve", actor_id=user.sub)
    return {"id": doc_id, "message": "휴가 신청이 승인되었습니다"}


@router.post(
    "/{doc_id}/reject",
    dependencies=[Depends(require_permission("leave_application:create"))],
)
def reject_leave_application(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """휴가 신청을 반려한다."""

    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    service = LeaveService(tenant_id=user.tenant_id)
    service.process_leave_application(doc_id, action="reject", actor_id=user.sub)
    return {"id": doc_id, "message": "휴가 신청이 반려되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("leave_application:delete"))],
)
def delete_leave_application(doc_id: str, user: CurrentUserDep) -> None:
    """휴가 신청을 삭제한다. OPEN 상태에서만 허용한다."""

    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None

    current_status = str(document.get("status", LeaveStatus.OPEN)).lower()
    if current_status != LeaveStatus.OPEN.value:
        raise_unprocessable(
            "ERR-HR-032",
            "OPEN 상태의 휴가 신청만 승인/거절/삭제할 수 있습니다",
        )

    repo.delete_by_id(doc_id)
