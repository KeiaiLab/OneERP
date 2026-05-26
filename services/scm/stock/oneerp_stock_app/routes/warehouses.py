"""창고(Warehouse) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.warehouse import Warehouse, WarehouseCreate, WarehouseUpdate

router = APIRouter(prefix="/api/v1/warehouses", tags=["창고"])

_COLLECTION = "warehouses"
_PREFIX = "WH"


def _get_repo() -> Repository:
    return Repository(_COLLECTION)


@router.post("/", status_code=201, dependencies=[Depends(require_permission("warehouse:create"))])
async def create_warehouse(body: WarehouseCreate) -> dict:
    """창고를 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    warehouse = Warehouse(
        _id=doc_id,
        warehouse_name=body.warehouse_name,
        warehouse_type=body.warehouse_type,
        parent_warehouse=body.parent_warehouse,
        is_group=body.is_group,
        company=body.company,
    )
    repo.insert(warehouse)
    return {"warehouse_id": doc_id, "message": "창고가 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("warehouse:read"))])
async def list_warehouses(page: int = 1, page_size: int = 20) -> dict:
    """창고 목록을 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(sort=[("warehouse_name", 1)], skip=skip, limit=page_size)
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("warehouse:read"))])
async def get_warehouse(doc_id: str) -> dict:
    """창고 상세를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="창고를 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("warehouse:write"))])
async def update_warehouse(doc_id: str, body: WarehouseUpdate) -> dict:
    """창고를 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="창고를 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    repo.update_by_id(doc_id, update_data)
    return {"message": "창고가 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("warehouse:delete"))])
async def delete_warehouse(doc_id: str) -> dict:
    """창고를 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="창고를 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "창고가 삭제되었습니다"}
