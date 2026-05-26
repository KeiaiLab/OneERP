"""로트(Batch) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.batch import Batch, BatchCreate

router = APIRouter(prefix="/api/v1/batches", tags=["로트"])

_COLLECTION = "batches"
_PREFIX = "BATCH"


def _get_repo() -> Repository:
    return Repository(_COLLECTION)


@router.post("/", status_code=201, dependencies=[Depends(require_permission("batche:create"))])
async def create_batch(body: BatchCreate) -> dict:
    """로트를 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    batch = Batch(
        _id=doc_id,
        batch_id=doc_id,
        item_code=body.item_code,
        manufacturing_date=body.manufacturing_date,
        expiry_date=body.expiry_date,
        supplier_ref=body.supplier_ref,
    )
    repo.insert(batch)
    return {"batch_id": doc_id, "message": "로트가 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("batche:read"))])
async def list_batches(
    page: int = 1,
    page_size: int = 20,
    item_code: str | None = None,
) -> dict:
    """로트 목록을 조회한다."""
    repo = _get_repo()
    query: dict = {}
    if item_code:
        query["item_code"] = item_code
    skip = (page - 1) * page_size
    data = repo.find_many(query, sort=[("_id", -1)], skip=skip, limit=page_size)
    total = repo.count(query)
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("batche:read"))])
async def get_batch(doc_id: str) -> dict:
    """로트 상세를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="로트를 찾을 수 없습니다")
    return doc
