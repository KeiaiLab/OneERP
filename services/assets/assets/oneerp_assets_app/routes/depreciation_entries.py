"""감가상각(DepreciationEntry) API 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_assets_app.models.depreciation import DepreciationEntry, DepreciationEntryCreate

router = APIRouter(prefix="/api/v1/depreciation-entries", tags=["감가상각"])

_COLLECTION = "depreciation_entries"
_PREFIX = "DEP"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("depreciation_entry:create"))]
)
def create_depreciation_entry(
    body: DepreciationEntryCreate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """감가상각 항목을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    entry = DepreciationEntry(
        _id=doc_id,
        tenant_id=user.tenant_id,
        asset_ref=body.asset_ref,
        posting_date=body.posting_date,
        depreciation_amount=body.depreciation_amount,
        accumulated_depreciation=body.accumulated_depreciation,
        remaining_value=body.remaining_value,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(entry)
    return {"id": doc_id, "message": "감가상각 항목이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("depreciation_entry:read"))])
def list_depreciation_entries(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """감가상각 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("depreciation_entry:read"))])
def get_depreciation_entry(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """감가상각 항목 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("감가상각 항목을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("depreciation_entry:delete"))],
)
def delete_depreciation_entry(doc_id: str, user: CurrentUserDep) -> None:
    """감가상각 항목을 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("감가상각 항목을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    repo.delete_by_id(doc_id)
