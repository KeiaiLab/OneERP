"""급여구조(SalaryStructure) API 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_payroll_app.models.salary_structure import (
    SalaryStructure,
    SalaryStructureCreate,
    SalaryStructureUpdate,
)

router = APIRouter(prefix="/api/v1/salary-structures", tags=["급여구조"])

_COLLECTION = "salary_structures"
_PREFIX = "SS"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("salary_structure:create"))]
)
def create_salary_structure(
    body: SalaryStructureCreate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """급여구조를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    structure = SalaryStructure(
        _id=doc_id,
        tenant_id=user.tenant_id,
        name=body.name,
        company=body.company,
        is_active=body.is_active,
        earnings=body.earnings,
        deductions=body.deductions,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(structure)
    return {"id": doc_id, "message": "급여구조가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("salary_structure:read"))])
def list_salary_structures(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """급여구조 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("salary_structure:read"))])
def get_salary_structure(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """급여구조 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("급여구조를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("salary_structure:write"))])
def update_salary_structure(
    doc_id: str,
    body: SalaryStructureUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """급여구조를 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("급여구조를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "급여구조가 수정되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("salary_structure:delete"))],
)
def delete_salary_structure(doc_id: str, user: CurrentUserDep) -> None:
    """급여구조를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("급여구조를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    repo.delete_by_id(doc_id)
