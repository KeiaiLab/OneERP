"""직급(Designation) 커스텀 라우터.

직급 체계를 정렬 순서대로 조회하고, 현재 재직 중인 직원이 사용하는 직급은 삭제하지 못하게 한다.
"""

from __future__ import annotations

from collections import Counter
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_hr_app.models.designation import Designation, DesignationCreate, DesignationUpdate

router = APIRouter(prefix="/api/v1/designations", tags=["직급"])

_COLLECTION = "designations"
_EMPLOYEE_COLLECTION = "employees"
_PREFIX = "DESG"
_NOT_FOUND_MESSAGE = "직급을 찾을 수 없습니다"


def _get_designation_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_employee_repo(tenant_id: str) -> Repository:
    return Repository(_EMPLOYEE_COLLECTION, tenant_id=tenant_id)


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    public = dict(document)
    if "_id" in public:
        public["id"] = public["_id"]
    return public


def _sort_designations(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        documents,
        key=lambda doc: (
            doc.get("rank_order", 0),
            doc.get("title", ""),
        ),
    )


def _is_current_employee(document: dict[str, Any]) -> bool:
    return str(document.get("status", "active")).lower() != "left"


@router.post("", status_code=201, dependencies=[Depends(require_permission("designation:create"))])
def create_designation(body: DesignationCreate, user: CurrentUserDep) -> dict[str, Any]:
    """직급을 생성한다."""
    repo = _get_designation_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    payload = body.model_dump()
    designation = Designation(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **payload,
    )
    repo.insert(designation)
    return {"_id": doc_id, "id": doc_id, **payload}


@router.get("", dependencies=[Depends(require_permission("designation:read"))])
def list_designations(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """직급 목록을 정렬 순서대로 조회한다."""
    repo = _get_designation_repo(user.tenant_id)
    documents = _sort_designations(repo.find_many(limit=1000))
    total = len(documents)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": [_with_public_id(doc) for doc in documents[start:end]],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/hierarchy", dependencies=[Depends(require_permission("designation:read"))])
def get_designation_hierarchy(user: CurrentUserDep) -> dict[str, Any]:
    """직급 체계를 정렬 순서와 현재 재직 인원 수와 함께 조회한다."""
    designation_repo = _get_designation_repo(user.tenant_id)
    employee_repo = _get_employee_repo(user.tenant_id)
    designations = _sort_designations(designation_repo.find_many(limit=1000))
    employees = employee_repo.find_many(limit=10000)
    employee_counts = Counter(
        employee.get("designation", "")
        for employee in employees
        if employee.get("designation") and _is_current_employee(employee)
    )

    data: list[dict[str, Any]] = []
    for designation in designations:
        public = _with_public_id(designation)
        public["employee_count"] = employee_counts.get(public.get("title", ""), 0)
        data.append(public)
    return {"data": data, "total": len(data)}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("designation:read"))])
def get_designation(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """직급 상세를 조회한다."""
    repo = _get_designation_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert doc is not None
    return _with_public_id(doc)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("designation:write"))])
def update_designation(
    doc_id: str,
    body: DesignationUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """직급을 수정한다."""
    repo = _get_designation_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert doc is not None
    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return _with_public_id({**doc, **update_data})


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("designation:delete"))]
)
def delete_designation(doc_id: str, user: CurrentUserDep) -> None:
    """현재 재직 중인 직원이 없을 때만 직급을 삭제한다."""
    repo = _get_designation_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert doc is not None

    employee_repo = _get_employee_repo(user.tenant_id)
    employees = employee_repo.find_many(limit=10000)
    in_use = any(
        employee.get("designation") == doc.get("title", "") and _is_current_employee(employee)
        for employee in employees
    )
    if in_use:
        raise_unprocessable("ERR-HR-034", "직급이 사용 중이라 삭제할 수 없습니다")
    repo.delete_by_id(doc_id)
