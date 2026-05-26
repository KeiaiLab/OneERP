"""재고조정(StockReconciliation) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.events.schemas import EventType
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.stock_reconciliation import (
    StockReconciliation,
    StockReconciliationCreate,
    StockReconciliationUpdate,
)

router = APIRouter(prefix="/api/v1/stock-reconciliations", tags=["재고조정"])

_COLLECTION = "stock_reconciliations"
_PREFIX = "SREC"


def _get_repo() -> Repository:
    """재고조정 컬렉션 Repository를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("stock_reconciliation:create"))]
)
def create_stock_reconciliation(body: StockReconciliationCreate) -> dict:
    """재고조정을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = StockReconciliation(
        posting_date=body.posting_date,
        purpose=body.purpose,
        items=body.items,
    )
    doc.id = doc_id
    repo.insert(doc)
    return {"id": doc_id, "message": "재고조정이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("stock_reconciliation:read"))])
def list_stock_reconciliations(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
) -> dict:
    """재고조정 목록을 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    docs = repo.find_many({}, skip=skip, limit=page_size)
    total = repo.count({})
    return {"data": docs, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("stock_reconciliation:read"))])
def get_stock_reconciliation(doc_id: str) -> dict:
    """재고조정을 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="재고조정을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("stock_reconciliation:write"))])
def update_stock_reconciliation(doc_id: str, body: StockReconciliationUpdate) -> dict:
    """재고조정을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="재고조정을 찾을 수 없습니다")
    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="no_update", detail="수정할 내용이 없습니다")
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "재고조정이 수정되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=200,
    dependencies=[Depends(require_permission("stock_reconciliation:delete"))],
)
def delete_stock_reconciliation(doc_id: str) -> dict:
    """재고조정을 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="재고조정을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"id": doc_id, "message": "재고조정이 삭제되었습니다"}


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("stock_reconciliation:submit"))]
)
def submit_stock_reconciliation(doc_id: str, user: CurrentUserDep) -> dict:
    """재고조정을 제출한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="재고조정을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 0:
        raise OneERPError(
            status_code=400, error="invalid_status", detail="초안 상태에서만 제출 가능"
        )
    repo.submit_with_event(
        doc_id,
        event_type=EventType.STOCK_RECONCILIATION_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {"message": "재고조정이 제출되었습니다"}


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("stock_reconciliation:cancel"))]
)
def cancel_stock_reconciliation(doc_id: str) -> dict:
    """재고조정을 취소한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="재고조정을 찾을 수 없습니다")
    if doc.get("docstatus", 0) != 1:
        raise OneERPError(status_code=400, error="invalid_status", detail="제출된 문서만 취소 가능")
    repo.cancel(doc_id)
    return {"message": "재고조정이 취소되었습니다"}
