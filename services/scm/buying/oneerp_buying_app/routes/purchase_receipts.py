"""구매입고(Purchase Receipt) 라우터."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.events.schemas import EventType
from oneerp_core.line_items import calculate_line_totals_with_qty
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_buying_app.models.purchase_receipt import (
    PurchaseReceipt,
    PurchaseReceiptCreate,
    PurchaseReceiptUpdate,
)

router = APIRouter(prefix="/api/v1/purchase-receipts", tags=["구매입고"])

_COLLECTION = "purchase_receipts"
_PREFIX = "PRCP"


def _get_repo(tenant_id: str) -> Repository:
    """구매입고 저장소를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_purchase_order_repo(tenant_id: str) -> Repository:
    """구매주문 저장소를 반환한다."""
    return Repository("purchase_orders", tenant_id=tenant_id)


def _get_purchase_invoice_repo(tenant_id: str) -> Repository:
    """구매송장 저장소를 반환한다."""
    return Repository("purchase_invoices", tenant_id=tenant_id)


def _normalize_receipt_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """라인 금액과 품질검사 상태를 저장용 형태로 정규화한다."""
    normalized_items, _, _ = calculate_line_totals_with_qty(items)
    for item in normalized_items:
        inspection_required = bool(item.get("inspection_required", False))
        item["inspection_required"] = inspection_required
        item["inspection_status"] = "pending" if inspection_required else "not_required"
        item["quality_inspection_id"] = str(item.get("quality_inspection_id", "")).strip()
    return normalized_items


def _derive_inspection_status(items: list[dict[str, Any]]) -> str:
    """헤더 품질검사 상태를 계산한다."""
    return "pending" if any(item.get("inspection_required") for item in items) else "not_required"


def _build_inspection_summary(items: list[dict[str, Any]]) -> dict[str, int]:
    """입고 라인의 검수 요약을 계산한다."""
    required_item_count = sum(1 for item in items if item.get("inspection_required"))
    pending_item_count = sum(
        1
        for item in items
        if item.get("inspection_required") and item.get("inspection_status") == "pending"
    )
    completed_item_count = max(required_item_count - pending_item_count, 0)
    return {
        "required_item_count": required_item_count,
        "pending_item_count": pending_item_count,
        "completed_item_count": completed_item_count,
    }


def _build_status_badge(doc: dict[str, Any]) -> str:
    """구매입고 상태 배지를 계산한다."""
    docstatus = int(doc.get("docstatus", 0) or 0)
    if docstatus == DocStatus.DRAFT:
        return "draft"
    if docstatus == DocStatus.CANCELLED:
        return "cancelled"
    if any(
        item.get("inspection_required") and item.get("inspection_status") == "pending"
        for item in doc.get("items", [])
    ):
        return "inspection_pending"
    return "submitted"


def _build_available_actions(doc: dict[str, Any]) -> list[str]:
    """사용자 시나리오 기준 다음 액션을 계산한다."""
    docstatus = int(doc.get("docstatus", 0) or 0)
    if docstatus == DocStatus.DRAFT:
        return ["submit", "delete"]

    if docstatus != DocStatus.SUBMITTED:
        return []

    actions = ["create_purchase_invoice", "cancel"]
    if doc.get("quality_inspection_ids"):
        actions.append("view_quality_inspections")
    return actions


def _enrich_receipt_document(document: dict[str, Any], tenant_id: str) -> dict[str, Any]:
    """상세/목록 응답에 운영 요약을 추가한다."""
    enriched = dict(document)
    receipt_id = str(enriched.get("_id", ""))
    items = [dict(item) for item in enriched.get("items", [])]
    invoice_repo = _get_purchase_invoice_repo(tenant_id)
    downstream_summary = {
        "purchase_invoice_draft_count": invoice_repo.count(
            query={"purchase_receipt_id": receipt_id, "docstatus": DocStatus.DRAFT}
        ),
        "purchase_invoice_submitted_count": invoice_repo.count(
            query={"purchase_receipt_id": receipt_id, "docstatus": DocStatus.SUBMITTED}
        ),
    }
    downstream_summary["has_downstream_documents"] = any(downstream_summary.values())
    enriched["id"] = receipt_id
    enriched["items"] = items
    enriched["inspection_summary"] = _build_inspection_summary(items)
    enriched["status_badge"] = _build_status_badge(enriched)
    enriched["downstream_summary"] = downstream_summary
    enriched["available_actions"] = _build_available_actions(enriched)
    return enriched


def _create_quality_inspections(
    receipt_doc: dict[str, Any], tenant_id: str, actor_sub: str
) -> tuple[list[str], list[dict[str, Any]], str]:
    """검수 대상 품목에 대한 incoming 품질검사 초안을 생성한다."""
    receipt_items = receipt_doc.get("items", [])
    if not any(item.get("inspection_required") for item in receipt_items):
        return [], receipt_items, "not_required"

    inspection_repo = Repository("quality_inspections", tenant_id=tenant_id)
    inspection_ids: list[str] = []
    updated_items: list[dict[str, Any]] = []

    for item in receipt_items:
        item_copy = dict(item)
        if not item_copy.get("inspection_required"):
            item_copy["inspection_status"] = "not_required"
            item_copy["quality_inspection_id"] = ""
            updated_items.append(item_copy)
            continue

        inspection_id = str(item_copy.get("quality_inspection_id", "")).strip()
        if not inspection_id:
            inspection_id = generate_name("QI", tenant_id=tenant_id)
            inspection_repo.insert(
                {
                    "_id": inspection_id,
                    "tenant_id": tenant_id,
                    "docstatus": DocStatus.DRAFT,
                    "reference_type": "purchase_receipt",
                    "reference_no": receipt_doc.get("_id", ""),
                    "inspection_type": "incoming",
                    "item_code": item_copy.get("item_code", ""),
                    "readings": [],
                    "result": "accepted",
                    "created_at": datetime.now(tz=UTC),
                    "updated_at": datetime.now(tz=UTC),
                    "created_by": actor_sub,
                    "updated_by": actor_sub,
                }
            )
        item_copy["quality_inspection_id"] = inspection_id
        item_copy["inspection_status"] = "pending"
        inspection_ids.append(inspection_id)
        updated_items.append(item_copy)

    return inspection_ids, updated_items, "pending"


def _validate_receipt_against_purchase_orders(receipt_doc: dict[str, Any], tenant_id: str) -> None:
    """참조 구매주문의 잔여 수량을 초과한 입고를 차단한다."""
    po_repo = _get_purchase_order_repo(tenant_id)
    po_cache: dict[str, dict[str, Any] | None] = {}

    for item in receipt_doc.get("items", []):
        purchase_order_id = str(item.get("purchase_order", "")).strip()
        if not purchase_order_id:
            continue
        po_doc = po_cache.get(purchase_order_id)
        if purchase_order_id not in po_cache:
            po_doc = po_repo.find_by_id(purchase_order_id)
            po_cache[purchase_order_id] = po_doc
        if not po_doc:
            raise_not_found(f"구매주문 '{purchase_order_id}'을 찾을 수 없습니다")

        purchase_order_item = next(
            (
                po_item
                for po_item in po_doc.get("items", [])
                if po_item.get("item_code") == item.get("item_code")
            ),
            None,
        )
        if not purchase_order_item:
            continue

        ordered_qty = Decimal(str(purchase_order_item.get("qty", 0) or 0))
        received_qty = Decimal(str(purchase_order_item.get("received_qty", 0) or 0))
        receipt_qty = Decimal(str(item.get("qty", 0) or 0))
        remaining_qty = max(ordered_qty - received_qty, Decimal(0))
        if receipt_qty > remaining_qty:
            raise_bad_request("ERR-BUY-048: 입고 수량이 발주 잔량을 초과할 수 없습니다")


def _update_po_received_qty(receipt_doc: dict[str, Any], tenant_id: str) -> None:
    """입고 아이템별로 참조 구매주문의 received_qty를 누적 갱신한다."""
    po_items_map: dict[str, dict[str, Decimal]] = {}
    for item in receipt_doc.get("items", []):
        po_id = str(item.get("purchase_order", "")).strip()
        if not po_id:
            continue
        item_code = str(item.get("item_code", "")).strip()
        qty = Decimal(str(item.get("qty", 0) or 0))
        po_items_map.setdefault(po_id, {})
        po_items_map[po_id][item_code] = po_items_map[po_id].get(item_code, Decimal(0)) + qty

    if not po_items_map:
        return

    po_repo = _get_purchase_order_repo(tenant_id)
    for po_id, item_qty_map in po_items_map.items():
        po_doc = po_repo.find_by_id(po_id)
        if not po_doc:
            continue
        updated = False
        po_items = [dict(item) for item in po_doc.get("items", [])]
        for po_item in po_items:
            code = str(po_item.get("item_code", "")).strip()
            if code not in item_qty_map:
                continue
            current = Decimal(str(po_item.get("received_qty", 0) or 0))
            po_item["received_qty"] = current + item_qty_map[code]
            updated = True
        if updated:
            po_repo.update_by_id(po_id, {"items": po_items})


def _coerce_date(value: Any) -> date:
    """문자열/date/datetime을 date로 정규화한다."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value:
        return date.fromisoformat(str(value))
    return datetime.now(tz=UTC).date()


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("purchase_receipt:create"))]
)
def 구매입고_생성(body: PurchaseReceiptCreate, user: CurrentUserDep) -> dict[str, Any]:
    """구매입고를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    items_raw = _normalize_receipt_items([item.model_dump() for item in body.items])
    _, total_qty, total_amount = calculate_line_totals_with_qty(items_raw)
    inspection_status = _derive_inspection_status(items_raw)

    receipt = PurchaseReceipt(
        _id=doc_id,
        tenant_id=user.tenant_id,
        supplier=body.supplier,
        supplier_name=body.supplier_name,
        posting_date=body.posting_date,
        items=body.items,
        total_qty=total_qty,
        total_amount=total_amount,
        warehouse=body.warehouse,
        inspection_status=inspection_status,
        quality_inspection_ids=[],
        created_by=user.sub,
        updated_by=user.sub,
    )
    doc_dict = receipt.model_dump(by_alias=True, exclude_none=True)
    doc_dict["items"] = items_raw
    repo.insert(doc_dict)

    return {"id": doc_id, "message": "구매입고가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("purchase_receipt:read"))])
def 구매입고_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """구매입고 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    docs = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = repo.count()
    return {
        "data": [_enrich_receipt_document(doc, user.tenant_id) for doc in docs],
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("purchase_receipt:read"))])
def 구매입고_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """구매입고 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found("구매입고를 찾을 수 없습니다")
    assert doc is not None
    return _enrich_receipt_document(doc, user.tenant_id)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("purchase_receipt:write"))])
def 구매입고_수정(
    doc_id: str,
    body: PurchaseReceiptUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """구매입고를 수정한다. 초안 상태에서만 허용한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found("구매입고를 찾을 수 없습니다")
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    if "items" in update_data:
        items_raw = _normalize_receipt_items(update_data["items"])
        _, total_qty, total_amount = calculate_line_totals_with_qty(items_raw)
        update_data["items"] = items_raw
        update_data["total_qty"] = total_qty
        update_data["total_amount"] = total_amount
        update_data["inspection_status"] = _derive_inspection_status(items_raw)
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "구매입고가 수정되었습니다"}


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("purchase_receipt:submit"))]
)
def 구매입고_제출(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """구매입고를 제출하고 품질검사/입고 수량을 동기화한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found("구매입고를 찾을 수 없습니다")
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    _validate_receipt_against_purchase_orders(doc, user.tenant_id)
    inspection_ids, updated_items, inspection_status = _create_quality_inspections(
        doc, user.tenant_id, user.sub
    )
    if inspection_ids or doc.get("inspection_status") != inspection_status:
        repo.update_by_id(
            doc_id,
            {
                "items": updated_items,
                "quality_inspection_ids": inspection_ids,
                "inspection_status": inspection_status,
                "updated_by": user.sub,
            },
        )
        doc["items"] = updated_items
        doc["quality_inspection_ids"] = inspection_ids
        doc["inspection_status"] = inspection_status

    _update_po_received_qty(doc, user.tenant_id)

    repo.submit_with_event(
        doc_id,
        event_type=EventType.PURCHASE_RECEIPT_SUBMITTED,
        event_data={
            "doc_id": doc_id,
            "inspection_status": inspection_status,
            "quality_inspection_ids": inspection_ids,
        },
        triggered_by=user.sub,
    )
    return {"id": doc_id, "message": "구매입고가 제출되었습니다"}


@router.post(
    "/{doc_id}/purchase-invoice",
    status_code=201,
    dependencies=[Depends(require_permission("purchase_invoice:create"))],
)
def 구매송장_초안_생성(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """제출된 구매입고에서 구매송장 초안을 생성한다."""
    receipt_repo = _get_repo(user.tenant_id)
    doc = receipt_repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found("구매입고를 찾을 수 없습니다")
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request("ERR-BUY-052: 제출된 구매입고에서만 구매송장을 생성할 수 있습니다")

    invoice_items: list[dict[str, Any]] = []
    for idx, item in enumerate(doc.get("items", []), start=1):
        qty = float(item.get("qty", 0) or 0)
        rate = float(item.get("rate", 0) or 0)
        amount = float(item.get("amount", 0) or 0) or qty * rate
        invoice_items.append(
            {
                "idx": idx,
                "item_code": item.get("item_code", ""),
                "item_name": item.get("item_name", ""),
                "qty": qty,
                "rate": rate,
                "amount": amount,
            }
        )

    if not invoice_items:
        raise_bad_request("ERR-BUY-053: 구매송장으로 복사할 입고 품목이 없습니다")

    posting_date = _coerce_date(doc.get("posting_date"))
    due_date = posting_date + timedelta(days=30)
    grand_total = sum(item["amount"] for item in invoice_items)
    invoice_id = generate_name("PI", tenant_id=user.tenant_id)
    invoice_doc = {
        "_id": invoice_id,
        "tenant_id": user.tenant_id,
        "purchase_order_id": doc.get("purchase_order_id", ""),
        "purchase_receipt_id": doc_id,
        "supplier_id": doc.get("supplier", ""),
        "supplier_name": doc.get("supplier_name", ""),
        "posting_date": posting_date,
        "due_date": due_date,
        "items": invoice_items,
        "taxes": [],
        "net_total": grand_total,
        "grand_total": grand_total,
        "outstanding_amount": grand_total,
        "docstatus": DocStatus.DRAFT,
        "created_by": user.sub,
        "updated_by": user.sub,
    }
    _get_purchase_invoice_repo(user.tenant_id).insert(invoice_doc)
    return {"id": invoice_id, "message": "구매송장 초안이 생성되었습니다"}


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("purchase_receipt:cancel"))]
)
def 구매입고_취소(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """구매입고를 취소한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found("구매입고를 찾을 수 없습니다")
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request("제출된 문서만 취소할 수 있습니다")

    repo.cancel(doc_id)
    return {"id": doc_id, "message": "구매입고가 취소되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("purchase_receipt:delete"))],
)
def 구매입고_삭제(doc_id: str, user: CurrentUserDep) -> None:
    """구매입고를 삭제한다. 초안 상태에서만 허용한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found("구매입고를 찾을 수 없습니다")
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 삭제할 수 있습니다")

    repo.delete_by_id(doc_id)
