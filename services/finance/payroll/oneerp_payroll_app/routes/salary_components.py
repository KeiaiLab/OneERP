"""급여항목(SalaryComponent) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.salary_component import (
    SalaryComponent,
    SalaryComponentCreate,
    SalaryComponentUpdate,
)

router = APIRouter(prefix="/api/v1/salary-components", tags=["급여항목"])
_COLLECTION = "salary_components"
_PREFIX = "SCMP"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("salary_component:create"))]
)
async def create_salary_component(body: SalaryComponentCreate) -> dict:
    """급여항목을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = SalaryComponent(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"salary_component_id": doc_id, "message": "급여항목이 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("salary_component:read"))])
async def list_salary_components(page: int = 1, page_size: int = 20) -> dict:
    """급여항목 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("salary_component:read"))])
async def get_salary_component(doc_id: str) -> dict:
    """급여항목 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="급여항목을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("salary_component:write"))])
async def update_salary_component(doc_id: str, body: SalaryComponentUpdate) -> dict:
    """급여항목을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="급여항목을 찾을 수 없습니다")
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "급여항목이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("salary_component:delete"))])
async def delete_salary_component(doc_id: str) -> dict:
    """급여항목을 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="급여항목을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "급여항목이 삭제되었습니다"}
