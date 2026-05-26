"""자산이동(AssetMovement) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.asset_movement import AssetMovement, AssetMovementCreate, AssetMovementUpdate

router = APIRouter(prefix="/api/v1/asset-movements", tags=["자산이동"])
_COLLECTION = "asset_movements"
_PREFIX = "AMOV"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("asset_movement:create"))]
)
async def create_asset_movement(body: AssetMovementCreate) -> dict:
    """자산이동을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = AssetMovement(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"asset_movement_id": doc_id, "message": "자산이동이 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("asset_movement:read"))])
async def list_asset_movements(page: int = 1, page_size: int = 20) -> dict:
    """자산이동 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("asset_movement:read"))])
async def get_asset_movement(doc_id: str) -> dict:
    """자산이동 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="자산이동을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("asset_movement:write"))])
async def update_asset_movement(doc_id: str, body: AssetMovementUpdate) -> dict:
    """자산이동을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="자산이동을 찾을 수 없습니다")
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "자산이동이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("asset_movement:delete"))])
async def delete_asset_movement(doc_id: str) -> dict:
    """자산이동을 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="자산이동을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "자산이동이 삭제되었습니다"}


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("asset_movement:submit"))]
)
async def submit_asset_movement(doc_id: str, user: CurrentUserDep) -> dict:
    """자산이동을 제출한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="자산이동을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(
            status_code=400, error="invalid_status", detail="초안 상태에서만 제출 가능"
        )
    repo.submit_with_event(
        doc_id, event_type=EventType.ASSET_MOVEMENT_SUBMITTED, triggered_by=user.sub
    )
    return {"message": "자산이동이 제출되었습니다"}


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("asset_movement:cancel"))]
)
async def cancel_asset_movement(doc_id: str) -> dict:
    """자산이동을 취소한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="자산이동을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 1:
        raise OneERPError(status_code=400, error="invalid_status", detail="제출된 문서만 취소 가능")
    repo.cancel(doc_id)
    return {"message": "자산이동이 취소되었습니다"}
