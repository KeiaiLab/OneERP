"""자산유형(AssetCategory) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.asset_category import AssetCategory, AssetCategoryCreate, AssetCategoryUpdate

router = APIRouter(prefix="/api/v1/asset-categories", tags=["자산유형"])
_COLLECTION = "asset_categories"
_PREFIX = "ACAT"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("asset_category:create"))]
)
async def create_asset_category(body: AssetCategoryCreate) -> dict:
    """자산유형을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = AssetCategory(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"asset_category_id": doc_id, "message": "자산유형이 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("asset_category:read"))])
async def list_asset_categories(page: int = 1, page_size: int = 20) -> dict:
    """자산유형 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("asset_category:read"))])
async def get_asset_category(doc_id: str) -> dict:
    """자산유형 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="자산유형을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("asset_category:write"))])
async def update_asset_category(doc_id: str, body: AssetCategoryUpdate) -> dict:
    """자산유형을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="자산유형을 찾을 수 없습니다")
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "자산유형이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("asset_category:delete"))])
async def delete_asset_category(doc_id: str) -> dict:
    """자산유형을 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="자산유형을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "자산유형이 삭제되었습니다"}
