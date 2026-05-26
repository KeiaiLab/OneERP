"""재고빈(Stock Bins) 조회 라우터 — 품목/창고별 현재 잔고 조회.

StockLedgerService가 내부적으로 관리하는 stock_bins 컬렉션을
API로 노출하여 E2E 흐름에서 재고 잔고를 검증할 수 있도록 한다.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

router = APIRouter(prefix="/api/v1/stock-bins", tags=["재고빈"])

_COLLECTION = "stock_bins"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.get("", dependencies=[Depends(require_permission("stock_bin:read"))])
def 재고빈_목록(
    user: CurrentUserDep,
    item_code: str | None = Query(None, description="품목 코드 필터"),
    warehouse: str | None = Query(None, description="창고 필터"),
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """재고빈 목록을 조회한다. item_code/warehouse로 필터링 가능."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if item_code:
        query["item_code"] = item_code
    if warehouse:
        query["warehouse"] = warehouse

    skip = (page - 1) * page_size
    docs = repo.find_many(query, skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = repo.count(query)

    # stock_bins의 current_qty를 actual_qty로도 노출 (E2E 호환)
    for doc in docs:
        if "current_qty" in doc and "actual_qty" not in doc:
            doc["actual_qty"] = doc["current_qty"]

    return {
        "data": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }
