"""넘버링규칙(NamingSeries) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.naming_series import NamingSeries, NamingSeriesCreate, NamingSeriesUpdate

router = APIRouter(prefix="/api/v1/naming-series", tags=["넘버링규칙"])
_COLLECTION = "naming_series"
_PREFIX = "NSRS"


def _get_repo(tenant_id: str = "") -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("naming_series:create"))]
)
async def create_naming_series(body: NamingSeriesCreate, user: CurrentUserDep) -> dict:
    """넘버링규칙을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    doc = NamingSeries(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"naming_series_id": doc_id, "message": "넘버링규칙이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("naming_series:read"))])
async def list_naming_series(user: CurrentUserDep, page: int = 1, page_size: int = 20) -> dict:
    """넘버링규칙 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("naming_series:read"))])
async def get_naming_series(doc_id: str, user: CurrentUserDep) -> dict:
    """넘버링규칙 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="넘버링규칙을 찾을 수 없습니다"
        )
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("naming_series:write"))])
async def update_naming_series(doc_id: str, body: NamingSeriesUpdate, user: CurrentUserDep) -> dict:
    """넘버링규칙을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="넘버링규칙을 찾을 수 없습니다"
        )
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "넘버링규칙이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("naming_series:delete"))])
async def delete_naming_series(doc_id: str, user: CurrentUserDep) -> dict:
    """넘버링규칙을 삭제한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="넘버링규칙을 찾을 수 없습니다"
        )
    repo.delete_by_id(doc_id)
    return {"message": "넘버링규칙이 삭제되었습니다"}
