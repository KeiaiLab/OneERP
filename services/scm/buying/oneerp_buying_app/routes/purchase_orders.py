"""구매주문(Purchase Order) CRUD 라우터."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request
from oneerp_core.events.schemas import EventType
from oneerp_core.line_items import calculate_line_totals
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from oneerp_core.route_helpers import (
    cancel_document,
    check_draft_status,
    delete_draft,
    get_or_404,
    submit_document,
)

from oneerp_buying_app.models.purchase_order import (
    PurchaseOrder,
    PurchaseOrderCreate,
    PurchaseOrderUpdate,
)
from oneerp_buying_app.services.purchase_pricing_service import PurchasePricingService
from oneerp_buying_app.services.purchase_process_service import PurchaseProcessService

router = APIRouter(prefix="/api/v1/purchase-orders", tags=["구매주문"])

_COLLECTION = "purchase_orders"
_PREFIX = "PO"
_NOT_FOUND = "구매주문을 찾을 수 없습니다"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_purchase_receipt_repo(tenant_id: str) -> Repository:
    """구매입고 저장소를 반환한다."""
    return Repository("purchase_receipts", tenant_id=tenant_id)


def _get_purchase_invoice_repo(tenant_id: str) -> Repository:
    """구매송장 저장소를 반환한다."""
    return Repository("purchase_invoices", tenant_id=tenant_id)


def _normalize_date_value(value: Any, *, fallback: Any = None) -> str | None:
    """date/datetime/문자열 입력을 ISO 날짜 문자열로 정규화한다."""
    candidate = value if value not in (None, "") else fallback
    if candidate in (None, ""):
        return None
    if isinstance(candidate, datetime):
        return candidate.date().isoformat()
    if isinstance(candidate, date):
        return candidate.isoformat()
    return str(candidate)


def _normalize_purchase_order_items(
    items: list[dict[str, Any]],
    *,
    default_delivery_date: Any,
) -> tuple[list[dict[str, Any]], Decimal]:
    """라인 합계와 납기일을 정규화한다."""
    if not items:
        raise_bad_request("ERR-BUY-047: 구매주문에는 최소 1개 품목이 필요합니다")

    normalized_items, total = calculate_line_totals(items)
    fallback_delivery_date = _normalize_date_value(default_delivery_date)
    for item in normalized_items:
        item["delivery_date"] = _normalize_date_value(
            item.get("delivery_date"),
            fallback=fallback_delivery_date,
        )
    return normalized_items, total


def _parse_date(value: Any) -> date | None:
    """문서의 날짜 필드를 date 객체로 파싱한다."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def _build_status_badge(*, docstatus: int, total_qty: float, received_qty: float) -> str:
    """구매주문 상태 배지를 계산한다."""
    if docstatus == 0:
        return "draft"
    if docstatus == 2:
        return "cancelled"
    if total_qty > 0 and received_qty >= total_qty:
        return "received"
    if received_qty > 0:
        return "partially_received"
    return "submitted"


def _build_delivery_status(
    *,
    docstatus: int,
    remaining_qty: float,
    next_delivery_date: str | None,
) -> str:
    """미결 발주의 납기 상태를 계산한다."""
    if docstatus != 1:
        return "not_applicable"
    if remaining_qty <= 0:
        return "completed"
    if not next_delivery_date:
        return "unscheduled"
    due_date = _parse_date(next_delivery_date)
    if due_date is None:
        return "unscheduled"
    if due_date < datetime.now(tz=UTC).date():
        return "overdue"
    return "scheduled"


def _enrich_purchase_order_document(document: dict[str, Any], tenant_id: str) -> dict[str, Any]:
    """문서 응답에 납기/하위문서 추적 요약을 추가한다."""
    enriched = dict(document)
    purchase_order_id = str(enriched.get("_id", ""))
    items = []
    total_qty = Decimal(0)
    total_received_qty = Decimal(0)
    open_delivery_dates: list[date] = []
    fallback_delivery_date = _normalize_date_value(enriched.get("transaction_date"))

    for raw_item in enriched.get("items", []):
        item = dict(raw_item)
        qty = Decimal(str(item.get("qty", 0) or 0))
        received_qty = Decimal(str(item.get("received_qty", 0) or 0))
        remaining_qty = max(qty - received_qty, Decimal(0))
        normalized_delivery_date = _normalize_date_value(
            item.get("delivery_date"),
            fallback=fallback_delivery_date,
        )
        if remaining_qty > 0 and normalized_delivery_date:
            due_date = _parse_date(normalized_delivery_date)
            if due_date is not None:
                open_delivery_dates.append(due_date)

        item["delivery_date"] = normalized_delivery_date
        item["remaining_qty"] = float(remaining_qty)
        items.append(item)
        total_qty += qty
        total_received_qty += min(received_qty, qty)

    remaining_qty = max(total_qty - total_received_qty, Decimal(0))
    receipt_completion_percent = Decimal(0)
    if total_qty > 0:
        receipt_completion_percent = (total_received_qty / total_qty) * Decimal(100)

    receipt_repo = _get_purchase_receipt_repo(tenant_id)
    invoice_repo = _get_purchase_invoice_repo(tenant_id)
    downstream_summary = {
        "purchase_receipt_draft_count": receipt_repo.count(
            query={"purchase_order_id": purchase_order_id, "docstatus": 0}
        ),
        "purchase_receipt_submitted_count": receipt_repo.count(
            query={"purchase_order_id": purchase_order_id, "docstatus": 1}
        ),
        "purchase_invoice_draft_count": invoice_repo.count(
            query={"purchase_order_id": purchase_order_id, "docstatus": 0}
        ),
        "purchase_invoice_submitted_count": invoice_repo.count(
            query={"purchase_order_id": purchase_order_id, "docstatus": 1}
        ),
    }
    downstream_summary["has_downstream_documents"] = any(downstream_summary.values())

    next_delivery_date = None
    if open_delivery_dates:
        next_delivery_date = min(open_delivery_dates).isoformat()

    docstatus = int(enriched.get("docstatus", 0) or 0)
    enriched["id"] = purchase_order_id
    enriched["items"] = items
    enriched["total_qty"] = float(total_qty)
    enriched["received_qty"] = float(total_received_qty)
    enriched["remaining_qty"] = float(remaining_qty)
    enriched["receipt_completion_percent"] = float(
        receipt_completion_percent.quantize(Decimal("0.01"))
    )
    enriched["next_delivery_date"] = next_delivery_date
    enriched["status_badge"] = _build_status_badge(
        docstatus=docstatus,
        total_qty=float(total_qty),
        received_qty=float(total_received_qty),
    )
    enriched["delivery_status"] = _build_delivery_status(
        docstatus=docstatus,
        remaining_qty=float(remaining_qty),
        next_delivery_date=next_delivery_date,
    )
    enriched["downstream_summary"] = downstream_summary
    return enriched


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("purchase_order:create"))]
)
def create_purchase_order(body: PurchaseOrderCreate, user: CurrentUserDep) -> dict[str, Any]:
    """구매주문을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    items_raw = [item.model_dump() for item in body.items]
    items_raw, total = _normalize_purchase_order_items(
        items_raw,
        default_delivery_date=body.transaction_date,
    )

    pricing_service = PurchasePricingService(tenant_id=user.tenant_id)
    pricing_result = pricing_service.apply_rules(items_raw, party=body.supplier_id)
    discount_total = Decimal(str(pricing_result["total_discount"]))

    purchase_order = PurchaseOrder(
        _id=doc_id,
        tenant_id=user.tenant_id,
        supplier_id=body.supplier_id,
        supplier_name=body.supplier_name,
        transaction_date=body.transaction_date,
        items=body.items,
        total=total,
        grand_total=total - discount_total,
        created_by=user.sub,
        updated_by=user.sub,
    )
    doc_dict = purchase_order.model_dump(by_alias=True, exclude_none=True)
    doc_dict["items"] = items_raw
    doc_dict["pricing_rules_applied"] = pricing_result["rules_applied"]
    doc_dict["discount_total"] = float(discount_total)
    repo.insert(doc_dict)

    return {"id": doc_id, "message": "구매주문이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("purchase_order:read"))])
def list_purchase_orders(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """구매주문 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    documents = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    return {
        "data": [
            _enrich_purchase_order_document(document, user.tenant_id) for document in documents
        ],
        "total": repo.count(),
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("purchase_order:read"))])
def get_purchase_order(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """구매주문 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    document = get_or_404(repo, doc_id, _NOT_FOUND)
    return _enrich_purchase_order_document(document, user.tenant_id)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("purchase_order:write"))])
def update_purchase_order(
    doc_id: str,
    body: PurchaseOrderUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """구매주문을 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    check_draft_status(doc, "수정")

    update_data = body.model_dump(exclude_none=True)
    if "items" in update_data:
        items_raw, total = _normalize_purchase_order_items(
            update_data["items"],
            default_delivery_date=body.transaction_date or doc.get("transaction_date"),
        )
        update_data["items"] = items_raw
        update_data["total"] = total
        update_data["grand_total"] = total
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "구매주문이 수정되었습니다"}


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("purchase_order:submit"))]
)
def submit_purchase_order(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """구매주문을 제출한다 (초안 -> 제출)."""
    repo = _get_repo(user.tenant_id)
    submit_document(repo, doc_id, _NOT_FOUND)

    repo.submit_with_event(
        doc_id,
        event_type=EventType.PURCHASE_ORDER_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {"id": doc_id, "message": "구매주문이 제출되었습니다"}


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("purchase_order:cancel"))]
)
def cancel_purchase_order(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """구매주문을 취소한다 (제출 -> 취소)."""
    repo = _get_repo(user.tenant_id)
    cancel_document(repo, doc_id, _NOT_FOUND)
    return {"id": doc_id, "message": "구매주문이 취소되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("purchase_order:delete"))],
)
def delete_purchase_order(doc_id: str, user: CurrentUserDep) -> None:
    """구매주문을 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    delete_draft(repo, doc_id, _NOT_FOUND)


@router.post(
    "/from-quotation/{quotation_id}",
    status_code=201,
    dependencies=[Depends(require_permission("purchase_order:create"))],
)
def create_purchase_order_from_quotation(
    quotation_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """제출된 공급업체견적에서 구매주문 초안을 생성한다."""
    service = PurchaseProcessService(user.tenant_id)
    result = service.create_po_from_quotation(quotation_id)
    return {
        "id": result["po_id"],
        "message": "구매주문 초안이 생성되었습니다",
        "quotation_reference": quotation_id,
    }


@router.post(
    "/{doc_id}/purchase-receipt",
    status_code=201,
    dependencies=[Depends(require_permission("purchase_receipt:create"))],
)
def create_purchase_receipt_from_purchase_order(
    doc_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """제출된 구매주문에서 구매입고 초안을 생성한다."""
    service = PurchaseProcessService(user.tenant_id)
    result = service.create_receipt_from_purchase_order(doc_id)
    return {
        "id": result["purchase_receipt_id"],
        "message": "구매입고 초안이 생성되었습니다",
        "purchase_order_id": doc_id,
    }


@router.post(
    "/{doc_id}/purchase-invoice",
    status_code=201,
    dependencies=[Depends(require_permission("purchase_invoice:create"))],
)
def create_purchase_invoice_from_purchase_order(
    doc_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """제출된 구매주문에서 구매송장 초안을 생성한다."""
    service = PurchaseProcessService(user.tenant_id)
    result = service.create_invoice_from_purchase_order(doc_id)
    return {
        "id": result["purchase_invoice_id"],
        "message": "구매송장 초안이 생성되었습니다",
        "purchase_order_id": doc_id,
    }
