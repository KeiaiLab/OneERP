"""자산(Asset) API 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_assets_app.models.asset import Asset, AssetCreate, AssetStatus, AssetUpdate

router = APIRouter(prefix="/api/v1/assets", tags=["자산"])

_COLLECTION = "assets"
_PREFIX = "ASSET"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("asset:create"))])
def create_asset(body: AssetCreate, user: CurrentUserDep) -> dict[str, Any]:
    """자산을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    asset = Asset(
        _id=doc_id,
        tenant_id=user.tenant_id,
        asset_name=body.asset_name,
        asset_category=body.asset_category,
        purchase_date=body.purchase_date,
        gross_amount=body.gross_amount,
        depreciation_method=body.depreciation_method,
        useful_life_years=body.useful_life_years,
        salvage_value=body.salvage_value,
        current_value=body.current_value,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(asset)
    return {"id": doc_id, "message": "자산이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("asset:read"))])
def list_assets(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """자산 목록을 페이지네이션으로 조회한다."""
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("asset:read"))])
def get_asset(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """자산 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자산을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("asset:write"))])
def update_asset(
    doc_id: str,
    body: AssetUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """자산 정보를 수정한다. draft 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자산을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    current_status = doc.get("status", AssetStatus.DRAFT)
    if current_status != AssetStatus.DRAFT:
        raise_bad_request("draft 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "자산 정보가 수정되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("asset:submit"))])
def submit_asset(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """자산을 제출한다 (draft -> submitted)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자산을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    current_status = doc.get("status", AssetStatus.DRAFT)
    if current_status != AssetStatus.DRAFT:
        raise_bad_request("draft 상태에서만 제출할 수 있습니다")

    repo.update_by_id(
        doc_id,
        {"status": AssetStatus.SUBMITTED, "updated_by": user.sub},
    )
    repo.submit_with_event(doc_id, event_type=EventType.ASSET_SUBMITTED, triggered_by=user.sub)
    return {"id": doc_id, "message": "자산이 제출되었습니다"}


@router.post("/{doc_id}/scrap", dependencies=[Depends(require_permission("asset:create"))])
def scrap_asset(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """자산을 폐기한다 (submitted -> scrapped)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자산을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    current_status = doc.get("status", AssetStatus.DRAFT)
    if current_status != AssetStatus.SUBMITTED:
        raise_bad_request("submitted 상태에서만 폐기할 수 있습니다")

    repo.update_by_id(
        doc_id,
        {"status": AssetStatus.SCRAPPED, "updated_by": user.sub},
    )
    return {"id": doc_id, "message": "자산이 폐기되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("asset:delete"))]
)
def delete_asset(doc_id: str, user: CurrentUserDep) -> None:
    """자산을 삭제한다. draft 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("자산을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조

    current_status = doc.get("status", AssetStatus.DRAFT)
    if current_status != AssetStatus.DRAFT:
        raise_bad_request("draft 상태의 자산만 삭제할 수 있습니다")

    repo.delete_by_id(doc_id)
