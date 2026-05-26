"""직원(Employee) 커스텀 라우터.

직원 마스터의 확장 필드, 보고라인 검증, 디렉터리 조회, 삭제 제약을 함께 제공한다.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.events.outbox import OutboxMixin
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_hr_app.models.employee import Employee, EmployeeCreate, EmployeeStatus, EmployeeUpdate

router = APIRouter(prefix="/api/v1/employees", tags=["직원"])

_COLLECTION = "employees"
_PREFIX = "EMP"
_NOT_FOUND_MESSAGE = "직원을 찾을 수 없습니다"


def _get_employee_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    public = dict(document)
    if "_id" in public:
        public["id"] = public["_id"]
    return public


def _validate_manager(
    repo: Repository,
    reports_to: str,
    *,
    current_employee_id: str | None = None,
) -> None:
    if not reports_to:
        return
    if current_employee_id and reports_to == current_employee_id:
        raise_unprocessable("ERR-HR-042", "본인을 보고 상사로 지정할 수 없습니다")
    manager = repo.find_by_id(reports_to)
    if not manager:
        raise_unprocessable("ERR-HR-041", "보고 상사 직원을 찾을 수 없습니다")


def _build_directory_payload(
    documents: list[dict[str, Any]],
    *,
    status: str | None = None,
    department: str | None = None,
    company: str | None = None,
) -> dict[str, Any]:
    employee_names = {
        document.get("_id", ""): document.get("employee_name", "")
        for document in documents
        if document.get("_id")
    }
    direct_report_counts = Counter(
        document.get("reports_to", "") for document in documents if document.get("reports_to")
    )
    summary = Counter(
        str(document.get("status", EmployeeStatus.ACTIVE.value)).lower() for document in documents
    )

    rows: list[dict[str, Any]] = []
    for document in documents:
        row = _with_public_id(document)
        row["manager_name"] = employee_names.get(document.get("reports_to", ""), "")
        row["direct_report_count"] = direct_report_counts.get(document.get("_id", ""), 0)
        rows.append(row)

    def _matches(row: dict[str, Any]) -> bool:
        if status and str(row.get("status", "")).lower() != status.lower():
            return False
        if department and row.get("department", "") != department:
            return False
        return not (company and row.get("company", "") != company)

    filtered = [row for row in rows if _matches(row)]
    filtered.sort(key=lambda row: (row.get("employee_name", ""), row.get("id", "")))
    return {
        "data": filtered,
        "total": len(filtered),
        "summary": {
            "active": summary.get(EmployeeStatus.ACTIVE.value, 0),
            "left": summary.get(EmployeeStatus.LEFT.value, 0),
            "suspended": summary.get(EmployeeStatus.SUSPENDED.value, 0),
        },
    }


@router.post("", status_code=201, dependencies=[Depends(require_permission("employee:create"))])
def create_employee(body: EmployeeCreate, user: CurrentUserDep) -> dict[str, Any]:
    """직원을 생성한다."""
    repo = _get_employee_repo(user.tenant_id)
    payload = body.model_dump(exclude_none=True)
    _validate_manager(repo, payload.get("reports_to", ""))

    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    outbox_entry = OutboxMixin.create_outbox_entry(
        event_type=EventType.EMPLOYEE_CREATED,
        doc_id=doc_id,
        tenant_id=user.tenant_id,
        data=payload,
        triggered_by=user.sub,
    )
    employee = Employee(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **payload,
    )
    document = employee.model_dump(by_alias=True, exclude_none=True)
    document["_outbox"] = [outbox_entry]
    repo.insert(document)
    return _with_public_id(document)


@router.get("", dependencies=[Depends(require_permission("employee:read"))])
def list_employees(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    status: str | None = None,
    department: str | None = None,
    company: str | None = None,
) -> dict[str, Any]:
    """직원 목록을 조회한다."""
    repo = _get_employee_repo(user.tenant_id)
    documents = repo.find_many(limit=1000, sort=[("employee_name", 1)])
    payload = _build_directory_payload(
        documents,
        status=status,
        department=department,
        company=company,
    )
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": payload["data"][start:end],
        "total": payload["total"],
        "page": page,
        "page_size": page_size,
    }


@router.get("/directory", dependencies=[Depends(require_permission("employee:read"))])
def get_employee_directory(
    user: CurrentUserDep,
    status: str | None = None,
    department: str | None = None,
    company: str | None = None,
) -> dict[str, Any]:
    """직원 디렉터리를 관리자/직속 인원 정보와 함께 조회한다."""
    repo = _get_employee_repo(user.tenant_id)
    documents = repo.find_many(limit=1000, sort=[("employee_name", 1)])
    return _build_directory_payload(
        documents,
        status=status,
        department=department,
        company=company,
    )


@router.get("/{doc_id}", dependencies=[Depends(require_permission("employee:read"))])
def get_employee(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """직원 상세를 조회한다."""
    repo = _get_employee_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    payload = _build_directory_payload([document])
    return payload["data"][0]


@router.put("/{doc_id}", dependencies=[Depends(require_permission("employee:write"))])
def update_employee(doc_id: str, body: EmployeeUpdate, user: CurrentUserDep) -> dict[str, Any]:
    """직원을 수정한다."""
    repo = _get_employee_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None

    update_data = body.model_dump(exclude_none=True)
    _validate_manager(repo, update_data.get("reports_to", ""), current_employee_id=doc_id)
    if not update_data:
        return _with_public_id(document)

    update_data["updated_by"] = user.sub
    repo.update_with_event(
        doc_id,
        update_data,
        event_type=EventType.EMPLOYEE_UPDATED,
        event_data=update_data,
        triggered_by=user.sub,
    )
    updated = {**document, **update_data}
    payload = _build_directory_payload([updated])
    return payload["data"][0]


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("employee:delete"))]
)
def delete_employee(doc_id: str, user: CurrentUserDep) -> None:
    """보고라인에 사용 중인 직원은 삭제하지 못하게 한다."""
    repo = _get_employee_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    if repo.count({"reports_to": doc_id}) > 0:
        raise_unprocessable("ERR-HR-043", "보고라인에 사용 중인 직원은 삭제할 수 없습니다")
    repo.delete_by_id(doc_id)
