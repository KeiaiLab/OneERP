"""재고원장(Stock Ledger Entry) 조회 라우터 — voucher_no 필터 지원.

EntityMeta 자동 CRUD 대신 커스텀 라우터로 관리하여
voucher_no 파라미터 필터링을 지원한다.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from pydantic import BaseModel, Field

from oneerp_stock_app.services.stock_ledger_service import StockLedgerService

router = APIRouter(prefix="/api/v1/stock-ledger-entries", tags=["재고 원장"])

_COLLECTION = "stock_ledger_entries"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_stock_ledger_service(tenant_id: str) -> StockLedgerService:
    """재고 원장 서비스를 생성한다."""
    return StockLedgerService(tenant_id)


class _ReceiptPayloadItem(BaseModel):
    item_code: str = Field(description="품목 코드")
    qty: float = Field(default=0, description="입고 수량")
    rate: float = Field(default=0, description="입고 단가")
    warehouse: str = Field(default="", description="창고")


class _ReceiptPayloadCreate(BaseModel):
    receipt_id: str
    tenant_id: str
    items: list[_ReceiptPayloadItem] = []


@router.get("", dependencies=[Depends(require_permission("stock_ledger_entry:read"))])
def 재고원장_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    voucher_no: str | None = Query(None, description="전표 번호 필터"),
    item_code: str | None = Query(None, description="품목 코드 필터"),
    warehouse: str | None = Query(None, description="창고 필터"),
) -> dict[str, Any]:
    """재고원장 목록을 조회한다. voucher_no/item_code/warehouse로 필터링 가능."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if voucher_no:
        query["voucher_no"] = voucher_no
    if item_code:
        query["item_code"] = item_code
    if warehouse:
        query["warehouse"] = warehouse

    skip = (page - 1) * page_size
    docs = repo.find_many(query, skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = repo.count(query)

    # qty_change → actual_qty 호환 매핑 (E2E 테스트 호환)
    for doc in docs:
        if "qty_change" in doc and "actual_qty" not in doc:
            doc["actual_qty"] = doc["qty_change"]

    return {
        "data": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.post("/from-purchase-receipt", status_code=201)
def 구매입고기준_재고원장_생성(body: _ReceiptPayloadCreate) -> dict[str, Any]:
    """이벤트 payload로 전달된 구매입고 기준 재고원장을 생성한다."""
    service = _get_stock_ledger_service(body.tenant_id)
    stock_ledger_entry_ids = service.process_receipt_payload(
        body.receipt_id,
        [item.model_dump() for item in body.items],
    )
    return {
        "receipt_id": body.receipt_id,
        "stock_ledger_entry_ids": stock_ledger_entry_ids,
        "message": "구매입고 기준 재고원장이 생성되었습니다",
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("stock_ledger_entry:read"))])
def 재고원장_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """재고원장 단건을 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        from oneerp_core.errors import raise_not_found

        raise_not_found("재고 원장을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    # actual_qty 호환 매핑
    if "qty_change" in doc and "actual_qty" not in doc:
        doc["actual_qty"] = doc["qty_change"]
    return doc
