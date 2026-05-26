"""재고이동(StockEntry) CRUD 라우터."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.stock_entry import StockEntry, StockEntryCreate, StockEntryUpdate

router = APIRouter(prefix="/api/v1/stock-entries", tags=["재고이동"])

_COLLECTION = "stock_entries"


def _get_repo(tenant_id: str) -> Repository:
    """재고이동 컬렉션 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("stock_entry:create"))])
def create_stock_entry(body: StockEntryCreate, user: CurrentUserDep) -> dict:
    """재고이동 문서를 생성한다."""
    repo = _get_repo(user.tenant_id)
    entry_id = generate_name("STE", tenant_id=user.tenant_id)
    entry = StockEntry(
        entry_id=entry_id,
        **body.model_dump(),
    )
    entry.id = entry_id
    repo.insert(entry)
    return {"entry_id": entry_id, "message": "재고이동이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("stock_entry:read"))])
def list_stock_entries(
    user: CurrentUserDep,
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    entry_type: str | None = Query(None, description="이동 유형 필터"),
) -> dict:
    """재고이동 목록을 조회한다 (페이지네이션 + entry_type 필터)."""
    repo = _get_repo(user.tenant_id)
    query: dict = {}
    if entry_type:
        query["entry_type"] = entry_type

    skip = (page - 1) * page_size
    entries = repo.find_many(query, skip=skip, limit=page_size)
    total = repo.count(query)
    return {
        "data": entries,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{entry_id}", dependencies=[Depends(require_permission("stock_entry:read"))])
def get_stock_entry(entry_id: str, user: CurrentUserDep) -> dict:
    """재고이동 문서를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(entry_id)
    if not doc:
        raise OneERPError(404, "재고이동을 찾을 수 없습니다", detail=f"entry_id={entry_id}")
    return doc


@router.put("/{entry_id}", dependencies=[Depends(require_permission("stock_entry:write"))])
def update_stock_entry(entry_id: str, body: StockEntryUpdate, user: CurrentUserDep) -> dict:
    """재고이동 문서를 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(entry_id)
    if not doc:
        raise OneERPError(404, "재고이동을 찾을 수 없습니다", detail=f"entry_id={entry_id}")

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(400, "수정할 내용이 없습니다")

    repo.update_by_id(entry_id, update_data)
    return {"entry_id": entry_id, "message": "재고이동이 수정되었습니다"}


@router.post("/{entry_id}/submit", dependencies=[Depends(require_permission("stock_entry:submit"))])
def submit_stock_entry(entry_id: str, user: CurrentUserDep) -> dict:
    """재고이동을 제출한다 (초안 -> 제출)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(entry_id)
    if not doc:
        raise OneERPError(404, "재고이동을 찾을 수 없습니다", detail=f"entry_id={entry_id}")
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(400, "초안 상태에서만 제출 가능")
    repo.submit_with_event(
        entry_id,
        event_type=EventType.STOCK_ENTRY_SUBMITTED,
        event_data={"doc_id": entry_id},
        triggered_by=user.sub,
    )
    return {"entry_id": entry_id, "message": "재고이동이 제출되었습니다"}


@router.delete(
    "/{entry_id}", status_code=200, dependencies=[Depends(require_permission("stock_entry:delete"))]
)
def delete_stock_entry(entry_id: str, user: CurrentUserDep) -> dict:
    """재고이동 문서를 삭제한다 (초안 상태만 가능)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(entry_id)
    if not doc:
        raise OneERPError(404, "재고이동을 찾을 수 없습니다", detail=f"entry_id={entry_id}")

    repo.delete_by_id(entry_id)
    return {"entry_id": entry_id, "message": "재고이동이 삭제되었습니다"}
