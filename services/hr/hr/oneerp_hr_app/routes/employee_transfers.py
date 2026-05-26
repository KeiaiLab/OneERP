"""인사발령(Employee Transfer) 워크벤치 라우터."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.events.outbox import OutboxMixin
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_hr_app.models.employee import EmployeeStatus
from oneerp_hr_app.models.employee_transfer import (
    EmployeeTransfer,
    EmployeeTransferCreate,
    EmployeeTransferUpdate,
)

router = APIRouter(prefix="/api/v1/employee-transfers", tags=["인사발령"])

_COLLECTION = "employee_transfers"
_EMPLOYEE_COLLECTION = "employees"
_DEPARTMENT_COLLECTION = "departments"
_DESIGNATION_COLLECTION = "designations"
_PREFIX = "ETR"
_NOT_FOUND_MESSAGE = "인사발령을 찾을 수 없습니다"


def _get_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_employee_repo(tenant_id: str) -> Repository:
    return Repository(_EMPLOYEE_COLLECTION, tenant_id=tenant_id)


def _get_department_repo(tenant_id: str) -> Repository:
    return Repository(_DEPARTMENT_COLLECTION, tenant_id=tenant_id)


def _get_designation_repo(tenant_id: str) -> Repository:
    return Repository(_DESIGNATION_COLLECTION, tenant_id=tenant_id)


def _iso_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value or "")


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    payload = dict(document)
    if "_id" in payload:
        payload["_id"] = str(payload["_id"])
        payload["id"] = payload["_id"]
    payload["transfer_date"] = _iso_date(payload.get("transfer_date"))
    return payload


def _find_named_document(repo: Repository, field_name: str, value: str) -> dict[str, Any] | None:
    if not value:
        return None
    rows = repo.find_many(query={field_name: value}, limit=1)
    return rows[0] if rows else None


def _validate_target_org(
    *,
    department_repo: Repository,
    designation_repo: Repository,
    to_department: str,
    to_designation: str,
) -> None:
    if to_department and not _find_named_document(
        department_repo, "department_name", to_department
    ):
        raise_unprocessable("ERR-HR-052", "이동 대상 부서를 찾을 수 없습니다")
    if to_designation and not _find_named_document(designation_repo, "title", to_designation):
        raise_unprocessable("ERR-HR-053", "이동 대상 직급을 찾을 수 없습니다")


def _resolve_employee(employee_repo: Repository, employee_id: str) -> dict[str, Any]:
    employee = employee_repo.find_by_id(employee_id)
    if not employee:
        raise_not_found(f"직원 '{employee_id}'을 찾을 수 없습니다")
    assert employee is not None
    return employee


def _change_scope(document: dict[str, Any]) -> str:
    department_changed = str(document.get("from_department", "")) != str(
        document.get("to_department", "")
    )
    designation_changed = str(document.get("from_designation", "")) != str(
        document.get("to_designation", "")
    )
    if department_changed and designation_changed:
        return "department_and_designation"
    if department_changed:
        return "department_only"
    if designation_changed:
        return "designation_only"
    return "no_change"


def _sync_summary(document: dict[str, Any], employee: dict[str, Any] | None) -> dict[str, Any]:
    outbox_entries = list(employee.get("_outbox", []) or []) if employee else []
    matched = [
        entry
        for entry in outbox_entries
        if str(entry.get("event_type", "")) == EventType.EMPLOYEE_UPDATED.value
        and str((entry.get("data") or {}).get("transfer_id", "")) == str(document.get("_id", ""))
    ]
    return {
        "employee_update_event_count": len(matched),
        "payroll_sync_pending": len(matched) > 0,
        "last_event_type": str(matched[-1].get("event_type", "")) if matched else "",
    }


def _status_badge(document: dict[str, Any], sync_summary: dict[str, Any]) -> str:
    if int(document.get("docstatus", DocStatus.DRAFT)) == int(DocStatus.CANCELLED):
        return "cancelled"
    if int(document.get("docstatus", DocStatus.DRAFT)) == int(DocStatus.DRAFT):
        return "draft_ready"

    scope = _change_scope(document)
    if scope == "department_and_designation":
        return "submitted_dual_change"
    if scope == "department_only":
        return "submitted_department_change"
    if scope == "designation_only":
        return "submitted_designation_change"
    if sync_summary["payroll_sync_pending"]:
        return "submitted_pending_sync"
    return "submitted"


def _recommended_action(document: dict[str, Any], sync_summary: dict[str, Any]) -> str:
    docstatus = int(document.get("docstatus", DocStatus.DRAFT))
    if docstatus == int(DocStatus.DRAFT):
        return "submit_transfer"
    if docstatus == int(DocStatus.CANCELLED):
        return "review_transfer_history"
    if sync_summary["payroll_sync_pending"]:
        return "verify_payroll_sync"
    return "review_employee_profile"


def _available_actions(document: dict[str, Any], sync_summary: dict[str, Any]) -> list[str]:
    docstatus = int(document.get("docstatus", DocStatus.DRAFT))
    if docstatus == int(DocStatus.DRAFT):
        return ["edit", "submit", "open_employee_profile"]
    if docstatus == int(DocStatus.CANCELLED):
        return ["open_employee_profile", "view_transfer_history"]
    actions = ["open_employee_profile"]
    if sync_summary["payroll_sync_pending"]:
        actions.append("verify_payroll_sync")
    actions.append("cancel")
    return actions


def _summary_payload(document: dict[str, Any], sync_summary: dict[str, Any]) -> dict[str, Any]:
    scope = _change_scope(document)
    return {
        "change_scope": scope,
        "department_changed": scope in {"department_and_designation", "department_only"},
        "designation_changed": scope in {"department_and_designation", "designation_only"},
        "transfer_date": _iso_date(document.get("transfer_date")),
        "payroll_sync_pending": sync_summary["payroll_sync_pending"],
    }


def _impact_summary(document: dict[str, Any], employee: dict[str, Any] | None) -> dict[str, Any]:
    scope = _change_scope(document)
    return {
        "employee_status": str(employee.get("status", "")) if employee else "",
        "department_changed": scope in {"department_and_designation", "department_only"},
        "designation_changed": scope in {"department_and_designation", "designation_only"},
        "current_department": str(employee.get("department", "")) if employee else "",
        "current_designation": str(employee.get("designation", "")) if employee else "",
    }


def _change_summary(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "change_scope": _change_scope(document),
        "from_department": str(document.get("from_department", "")),
        "to_department": str(document.get("to_department", "")),
        "from_designation": str(document.get("from_designation", "")),
        "to_designation": str(document.get("to_designation", "")),
        "transfer_date": _iso_date(document.get("transfer_date")),
    }


def _decorate_transfer(document: dict[str, Any], employee: dict[str, Any] | None) -> dict[str, Any]:
    payload = _with_public_id(document)
    sync_summary = _sync_summary(document, employee)
    payload["status_badge"] = _status_badge(document, sync_summary)
    payload["recommended_action"] = _recommended_action(document, sync_summary)
    payload["available_actions"] = _available_actions(document, sync_summary)
    payload["summary"] = _summary_payload(document, sync_summary)
    payload["employee_name"] = (
        str(payload.get("employee_name", "")) or str(employee.get("employee_name", ""))
        if employee
        else ""
    )
    return payload


def _build_workbench_summary(documents: list[dict[str, Any]]) -> dict[str, Any]:
    today = datetime.now(tz=UTC).date().isoformat()
    return {
        "draft_count": sum(
            1 for row in documents if int(row.get("docstatus", 0)) == int(DocStatus.DRAFT)
        ),
        "submitted_count": sum(
            1 for row in documents if int(row.get("docstatus", 0)) == int(DocStatus.SUBMITTED)
        ),
        "cancelled_count": sum(
            1 for row in documents if int(row.get("docstatus", 0)) == int(DocStatus.CANCELLED)
        ),
        "effective_today_count": sum(
            1
            for row in documents
            if int(row.get("docstatus", 0)) == int(DocStatus.SUBMITTED)
            and row["summary"]["transfer_date"] == today
        ),
        "payroll_sync_pending_count": sum(
            1 for row in documents if row["summary"]["payroll_sync_pending"]
        ),
    }


def _matches_filters(
    document: dict[str, Any], *, employee_id: str | None, status_badge: str | None
) -> bool:
    if employee_id and str(document.get("employee", "")) != employee_id:
        return False
    return not status_badge or str(document.get("status_badge", "")) == status_badge


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("employee_transfer:create"))]
)
def create_employee_transfer(body: EmployeeTransferCreate, user: CurrentUserDep) -> dict[str, Any]:
    """인사발령 초안을 생성한다."""
    payload = body.model_dump(exclude_none=True)
    employee_repo = _get_employee_repo(user.tenant_id)
    employee = _resolve_employee(employee_repo, payload["employee"])
    if str(employee.get("status", EmployeeStatus.ACTIVE.value)) != EmployeeStatus.ACTIVE.value:
        raise_unprocessable("ERR-HR-051", "재직 중인 직원만 인사발령할 수 있습니다")

    _validate_target_org(
        department_repo=_get_department_repo(user.tenant_id),
        designation_repo=_get_designation_repo(user.tenant_id),
        to_department=str(payload.get("to_department", "")),
        to_designation=str(payload.get("to_designation", "")),
    )

    current_department = str(employee.get("department", ""))
    current_designation = str(employee.get("designation", ""))
    target_department = str(payload.get("to_department", "") or current_department)
    target_designation = str(payload.get("to_designation", "") or current_designation)
    if target_department == current_department and target_designation == current_designation:
        raise_unprocessable("ERR-HR-003", "부서 또는 직위 중 1개 이상 변경해야 합니다")

    document = EmployeeTransfer(
        _id=generate_name(_PREFIX, tenant_id=user.tenant_id),
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        employee=payload["employee"],
        employee_name=str(payload.get("employee_name", "") or employee.get("employee_name", "")),
        transfer_date=payload.get("transfer_date"),
        from_department=current_department,
        to_department=target_department,
        from_designation=current_designation,
        to_designation=target_designation,
        reason=str(payload.get("reason", "")),
    ).model_dump(by_alias=True, exclude_none=True)
    _get_repo(user.tenant_id).insert(document)
    return _decorate_transfer(document, employee)


@router.get("", dependencies=[Depends(require_permission("employee_transfer:read"))])
def list_employee_transfers(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    employee: str | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """인사발령 워크벤치 목록을 조회한다."""
    repo = _get_repo(user.tenant_id)
    employee_repo = _get_employee_repo(user.tenant_id)
    documents = repo.find_many(sort=[("transfer_date", -1), ("created_at", -1)], limit=1000)
    decorated: list[dict[str, Any]] = []
    for document in documents:
        employee_doc = employee_repo.find_by_id(str(document.get("employee", "")))
        row = _decorate_transfer(document, employee_doc)
        if _matches_filters(row, employee_id=employee, status_badge=status_badge):
            decorated.append(row)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": decorated[start:end],
        "total": len(decorated),
        "page": page,
        "page_size": page_size,
        "summary": _build_workbench_summary(decorated),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("employee_transfer:read"))])
def get_employee_transfer(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """인사발령 상세를 조회한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    employee = _get_employee_repo(user.tenant_id).find_by_id(str(document.get("employee", "")))
    return _decorate_transfer(document, employee)


@router.get(
    "/{doc_id}/summary", dependencies=[Depends(require_permission("employee_transfer:read"))]
)
def get_employee_transfer_summary(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """인사발령 영향도와 급여 연계 요약을 반환한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    employee = _get_employee_repo(user.tenant_id).find_by_id(str(document.get("employee", "")))
    payload = _decorate_transfer(document, employee)
    payload["change_summary"] = _change_summary(document)
    payload["impact_summary"] = _impact_summary(document, employee)
    payload["sync_summary"] = _sync_summary(document, employee)
    return payload


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("employee_transfer:write"))]
)
def submit_employee_transfer(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """초안 인사발령을 제출하고 직원 마스터를 갱신한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    if int(document.get("docstatus", DocStatus.DRAFT)) != int(DocStatus.DRAFT):
        raise_unprocessable("ERR-HR-054", "초안 인사발령만 제출할 수 있습니다")

    employee_repo = _get_employee_repo(user.tenant_id)
    employee = _resolve_employee(employee_repo, str(document.get("employee", "")))
    update_data = {
        "department": str(document.get("to_department", "")),
        "designation": str(document.get("to_designation", "")),
    }
    employee_repo.update_by_id(str(document["employee"]), update_data)
    outbox_entry = OutboxMixin.create_outbox_entry(
        event_type=EventType.EMPLOYEE_UPDATED,
        doc_id=str(document["employee"]),
        tenant_id=user.tenant_id,
        data={
            "employee_id": str(document["employee"]),
            "department": update_data["department"],
            "designation": update_data["designation"],
            "transfer_id": str(document["_id"]),
        },
        triggered_by=user.sub,
    )
    employee_repo.update_by_id(str(document["employee"]), {"$push": {"_outbox": outbox_entry}})
    repo.update_by_id(doc_id, {"docstatus": DocStatus.SUBMITTED, "updated_by": user.sub})

    updated_employee = {
        **employee,
        **update_data,
        "_outbox": [*(employee.get("_outbox", []) or []), outbox_entry],
    }
    updated_document = {**document, "docstatus": int(DocStatus.SUBMITTED), "updated_by": user.sub}
    return _decorate_transfer(updated_document, updated_employee)


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("employee_transfer:write"))]
)
def cancel_employee_transfer(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """제출된 인사발령을 취소하고 직원 마스터를 원복한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    if int(document.get("docstatus", DocStatus.DRAFT)) != int(DocStatus.SUBMITTED):
        raise_unprocessable("ERR-HR-056", "제출된 인사발령만 취소할 수 있습니다")

    employee_repo = _get_employee_repo(user.tenant_id)
    employee = _resolve_employee(employee_repo, str(document.get("employee", "")))
    revert_data = {
        "department": str(document.get("from_department", "")),
        "designation": str(document.get("from_designation", "")),
    }
    employee_repo.update_by_id(str(document["employee"]), revert_data)
    outbox_entry = OutboxMixin.create_outbox_entry(
        event_type=EventType.EMPLOYEE_UPDATED,
        doc_id=str(document["employee"]),
        tenant_id=user.tenant_id,
        data={
            "employee_id": str(document["employee"]),
            "department": revert_data["department"],
            "designation": revert_data["designation"],
            "transfer_id": str(document["_id"]),
            "cancelled": True,
        },
        triggered_by=user.sub,
    )
    employee_repo.update_by_id(str(document["employee"]), {"$push": {"_outbox": outbox_entry}})
    repo.update_by_id(doc_id, {"docstatus": DocStatus.CANCELLED, "updated_by": user.sub})

    updated_employee = {
        **employee,
        **revert_data,
        "_outbox": [*(employee.get("_outbox", []) or []), outbox_entry],
    }
    updated_document = {**document, "docstatus": int(DocStatus.CANCELLED), "updated_by": user.sub}
    return _decorate_transfer(updated_document, updated_employee)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("employee_transfer:write"))])
def update_employee_transfer(
    doc_id: str, body: EmployeeTransferUpdate, user: CurrentUserDep
) -> dict[str, Any]:
    """초안 인사발령만 수정한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    if int(document.get("docstatus", DocStatus.DRAFT)) != int(DocStatus.DRAFT):
        raise_unprocessable("ERR-HR-057", "초안 인사발령만 수정할 수 있습니다")

    payload = body.model_dump(exclude_none=True)
    employee_repo = _get_employee_repo(user.tenant_id)
    employee = _resolve_employee(employee_repo, str(document.get("employee", "")))
    _validate_target_org(
        department_repo=_get_department_repo(user.tenant_id),
        designation_repo=_get_designation_repo(user.tenant_id),
        to_department=str(payload.get("to_department", document.get("to_department", ""))),
        to_designation=str(payload.get("to_designation", document.get("to_designation", ""))),
    )

    current_department = str(document.get("from_department", employee.get("department", "")))
    current_designation = str(document.get("from_designation", employee.get("designation", "")))
    target_department = str(
        payload.get("to_department", document.get("to_department", current_department))
        or current_department
    )
    target_designation = str(
        payload.get("to_designation", document.get("to_designation", current_designation))
        or current_designation
    )
    if target_department == current_department and target_designation == current_designation:
        raise_unprocessable("ERR-HR-003", "부서 또는 직위 중 1개 이상 변경해야 합니다")

    update_data = {
        **payload,
        "employee_name": str(
            payload.get(
                "employee_name", document.get("employee_name", employee.get("employee_name", ""))
            )
        ),
        "to_department": target_department,
        "to_designation": target_designation,
        "updated_by": user.sub,
    }
    repo.update_by_id(doc_id, update_data)
    updated_document = {**document, **update_data}
    return _decorate_transfer(updated_document, employee)


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("employee_transfer:delete"))],
)
def delete_employee_transfer(doc_id: str, user: CurrentUserDep) -> None:
    """초안 인사발령만 삭제한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    if int(document.get("docstatus", DocStatus.DRAFT)) != int(DocStatus.DRAFT):
        raise_unprocessable("ERR-HR-055", "초안 인사발령만 삭제할 수 있습니다")
    repo.delete_by_id(doc_id)
