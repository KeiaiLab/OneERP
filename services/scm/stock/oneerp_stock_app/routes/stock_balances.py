"""재고잔액(StockBalance) 리포트 라우트 — 읽기 전용."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

router = APIRouter(prefix="/api/v1/stock-balances", tags=["재고잔액"])

_COLLECTION = "stock_balances"


def _get_repo() -> Repository:
    """재고잔액 컬렉션 Repository를 반환한다."""
    return Repository(_COLLECTION)


@router.get("", dependencies=[Depends(require_permission("stock_balance:read"))])
def list_stock_balances(
    page: int = Query(1, ge=1, description="페이지 번호"),
    page_size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    item_code: str | None = Query(None, description="품목코드 필터"),
    warehouse: str | None = Query(None, description="창고 필터"),
) -> dict:
    """재고잔액 리포트를 조회한다."""
    repo = _get_repo()
    query: dict = {}
    if item_code:
        query["item_code"] = item_code
    if warehouse:
        query["warehouse"] = warehouse

    skip = (page - 1) * page_size
    docs = repo.find_many(query, skip=skip, limit=page_size)
    total = repo.count(query)
    return {"data": docs, "total": total, "page": page, "page_size": page_size}
