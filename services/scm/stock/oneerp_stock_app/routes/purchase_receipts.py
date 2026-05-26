"""입고전표(Purchase Receipt) CRUD 라우터 — stock 서비스 내 입고 처리.

E2E 흐름에서 stock 서비스가 입고전표를 직접 생성·제출한다.
제출 시 PURCHASE_RECEIPT_SUBMITTED 이벤트를 발행하여
재고 원장(StockLedgerService)이 재고를 반영한다.

OE002: Repository 접근은 PurchaseReceiptService 내부에서만 수행한다.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission

from oneerp_stock_app.dto import PurchaseReceiptCreate
from oneerp_stock_app.services.purchase_receipt_service import PurchaseReceiptService

router = APIRouter(prefix="/api/v1/purchase-receipts", tags=["입고전표"])

_PREFIX = "PRCP"


def get_service(user: CurrentUserDep) -> PurchaseReceiptService:
    """요청 테넌트에 바인딩된 PurchaseReceiptService를 생성한다."""
    return PurchaseReceiptService(user.tenant_id)


PurchaseReceiptServiceDep = Annotated[PurchaseReceiptService, Depends(get_service)]


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("purchase_receipt:create"))]
)
def 입고전표_생성(
    body: PurchaseReceiptCreate,
    user: CurrentUserDep,
    service: PurchaseReceiptServiceDep,
) -> dict[str, Any]:
    """입고전표를 생성한다."""
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    items_raw = [item.model_dump() for item in body.items]
    for item in items_raw:
        item["amount"] = item.get("qty", 0) * item.get("rate", 0.0)

    total_qty = sum(item.get("qty", 0) for item in items_raw)
    total_amount = sum(item.get("amount", 0.0) for item in items_raw)

    payload = {
        "supplier_name": body.supplier_name,
        "posting_date": body.posting_date,
        "purchase_order_id": body.purchase_order_id or "",
        "items": items_raw,
        "total_qty": total_qty,
        "total_amount": total_amount,
    }
    service.create(doc_id, payload, created_by=user.sub)

    return {"id": doc_id, "message": "입고전표가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("purchase_receipt:read"))])
def 입고전표_목록(
    service: PurchaseReceiptServiceDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """입고전표 목록을 페이지네이션으로 조회한다."""
    skip = (page - 1) * page_size
    docs = service.list(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = service.count()
    return {
        "data": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("purchase_receipt:read"))])
def 입고전표_조회(doc_id: str, service: PurchaseReceiptServiceDep) -> dict[str, Any]:
    """입고전표 상세 정보를 조회한다."""
    doc = service.get(doc_id)
    if not doc:
        raise_not_found("입고전표를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("purchase_receipt:submit"))]
)
def 입고전표_제출(
    doc_id: str,
    user: CurrentUserDep,
    service: PurchaseReceiptServiceDep,
) -> dict[str, Any]:
    """입고전표를 제출한다 (초안 → 제출)."""
    doc = service.get(doc_id)
    if not doc:
        raise_not_found("입고전표를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    service.submit(doc_id, triggered_by=user.sub)
    return {"id": doc_id, "message": "입고전표가 제출되었습니다"}
