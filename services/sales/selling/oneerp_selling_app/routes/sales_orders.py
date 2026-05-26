"""판매주문(Sales Order) API 라우터."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request
from oneerp_core.events.schemas import EventType
from oneerp_core.line_items import calculate_line_totals, calculate_line_totals_with_taxes
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.route_helpers import (
    cancel_document,
    check_draft_status,
    delete_draft,
    get_or_404,
    paginated_list,
    submit_document,
)
from pydantic import BaseModel

from oneerp_selling_app.dto import SalesOrderCreate, SalesOrderUpdate
from oneerp_selling_app.models.delivery_note import DeliveryNote, DeliveryNoteItem
from oneerp_selling_app.models.sales_invoice import SalesInvoice, SalesInvoiceItem, SalesInvoiceTax
from oneerp_selling_app.models.sales_order import SalesOrder, SalesOrderItem
from oneerp_selling_app.services.sales_order_service import SalesOrderRepoService
from oneerp_selling_app.services.sales_partner_snapshot import resolve_sales_partner_snapshot

router = APIRouter(prefix="/api/v1/sales-orders", tags=["판매주문"])

_COLLECTION = "sales_orders"
_PREFIX = "SO"
_NOT_FOUND = "판매주문을 찾을 수 없습니다"
_DELIVERY_NOTE_PREFIX = "DN"
_SALES_INVOICE_PREFIX = "SINV"


def _get_repo(tenant_id: str):  # type: ignore[no-untyped-def]
    """판매주문 Repository — Route→Service 은닉 후 호환 shim."""
    return SalesOrderRepoService(tenant_id).orders


def _get_delivery_note_repo(tenant_id: str):  # type: ignore[no-untyped-def]
    """판매주문 전환용 납품서 Repository 호환 shim."""
    return SalesOrderRepoService(tenant_id).delivery_notes


def _get_sales_invoice_repo(tenant_id: str):  # type: ignore[no-untyped-def]
    """판매주문 전환용 판매송장 Repository 호환 shim."""
    return SalesOrderRepoService(tenant_id).sales_invoices


class SalesOrderDeliveryNoteCreate(BaseModel):
    """판매주문에서 납품서 초안을 생성할 때의 입력."""

    posting_date: date | None = None
    warehouse: str | None = None
    transporter: str | None = None


class SalesOrderInvoiceCreate(BaseModel):
    """판매주문에서 판매송장 초안을 생성할 때의 입력."""

    posting_date: date | None = None
    due_date: date | None = None
    taxes: list[SalesInvoiceTax] = []
    etax_invoice_ref: str | None = None


def _normalize_sales_invoice_taxes(taxes: list[dict[str, Any]]) -> list[SalesInvoiceTax]:
    return [
        SalesInvoiceTax(
            tax_type=str(tax.get("tax_type", "") or ""),
            rate=Decimal(str(tax.get("rate", 0) or 0)),
            amount=Decimal(str(tax.get("amount", 0) or 0)),
        )
        for tax in taxes
    ]


def _coerce_order_date(value: Any) -> date | None:
    """문서 dict에 저장된 날짜 값을 date로 정규화한다."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    return None


def _validate_sales_order_payload(
    transaction_date: date | None,
    delivery_date: date | None,
    items: list[dict[str, Any]] | list[SalesOrderItem],
) -> None:
    """판매주문 핵심 입력 규칙을 검증한다."""
    if not items:
        raise_bad_request("ERR-SELL-048: 판매주문 품목은 1건 이상이어야 합니다")
    if (
        transaction_date is not None
        and delivery_date is not None
        and delivery_date < transaction_date
    ):
        raise_bad_request("ERR-SELL-047: 납품예정일은 거래일보다 빠를 수 없습니다")


def _normalize_downstream_refs(value: Any) -> dict[str, list[str]]:
    """후속 문서 추적 필드를 항상 동일한 구조로 정규화한다."""
    refs = value if isinstance(value, dict) else {}
    return {
        "delivery_note_ids": list(refs.get("delivery_note_ids") or []),
        "sales_invoice_ids": list(refs.get("sales_invoice_ids") or []),
    }


def _build_downstream_summary(refs: dict[str, list[str]]) -> dict[str, Any]:
    """판매주문 상세/목록에서 사용할 후속 문서 요약을 계산한다."""
    delivery_note_count = len(refs["delivery_note_ids"])
    sales_invoice_count = len(refs["sales_invoice_ids"])
    return {
        "delivery_note_count": delivery_note_count,
        "sales_invoice_count": sales_invoice_count,
        "has_downstream_documents": delivery_note_count + sales_invoice_count > 0,
    }


def _status_badge(docstatus: Any) -> str:
    """문서 상태를 UI 배지용 문자열로 정규화한다."""
    if docstatus in {DocStatus.SUBMITTED, 1, "submitted", "Submitted"}:
        return "submitted"
    if docstatus in {DocStatus.CANCELLED, 2, "cancelled", "Cancelled"}:
        return "cancelled"
    return "draft"


def _build_sales_order_response(doc: dict[str, Any]) -> dict[str, Any]:
    """판매주문 응답에 상태 배지와 후속 문서 요약을 주입한다."""
    payload = dict(doc)
    refs = _normalize_downstream_refs(payload.get("downstream_refs"))
    payload["downstream_refs"] = refs
    payload["status_badge"] = _status_badge(payload.get("docstatus"))
    payload["downstream_summary"] = _build_downstream_summary(refs)
    return payload


def _append_downstream_ref(
    refs: dict[str, list[str]],
    key: str,
    document_id: str,
) -> dict[str, list[str]]:
    """후속 문서 ID를 중복 없이 append 한다."""
    current = _normalize_downstream_refs(refs)
    if document_id not in current[key]:
        current[key].append(document_id)
    return current


def _require_submitted_sales_order(doc: dict[str, Any], action_name: str) -> None:
    """제출된 판매주문에서만 downstream 문서를 생성하도록 제한한다."""
    if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request(f"제출된 판매주문에서만 {action_name}를 생성할 수 있습니다")


@router.post("", status_code=201, dependencies=[Depends(require_permission("sales_order:create"))])
def create_sales_order(body: SalesOrderCreate, user: CurrentUserDep) -> dict[str, Any]:
    """판매주문을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    items_raw = [item.model_dump() for item in body.items]
    _validate_sales_order_payload(body.transaction_date, body.delivery_date, items_raw)
    items_raw, total = calculate_line_totals(items_raw)

    sales_order = SalesOrder(
        _id=doc_id,
        tenant_id=user.tenant_id,
        customer_id=body.customer_id,
        customer_name=body.customer_name,
        **resolve_sales_partner_snapshot(user.tenant_id, body.customer_id),
        transaction_date=body.transaction_date,
        delivery_date=body.delivery_date,
        items=[SalesOrderItem(**item) for item in items_raw],
        total=total,
        grand_total=total,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(sales_order)

    return {"id": doc_id, "message": "판매주문이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("sales_order:read"))])
def list_sales_orders(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """판매주문 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    payload = paginated_list(repo, page, page_size)
    payload["data"] = [_build_sales_order_response(doc) for doc in payload["data"]]
    return payload


@router.get("/{doc_id}", dependencies=[Depends(require_permission("sales_order:read"))])
def get_sales_order(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """판매주문 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    return _build_sales_order_response(get_or_404(repo, doc_id, _NOT_FOUND))


@router.put("/{doc_id}", dependencies=[Depends(require_permission("sales_order:write"))])
def update_sales_order(
    doc_id: str,
    body: SalesOrderUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """판매주문을 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    check_draft_status(doc, "수정")

    update_data = body.model_dump(exclude_none=True)
    effective_transaction_date = update_data.get(
        "transaction_date",
        _coerce_order_date(doc.get("transaction_date")),
    )
    effective_delivery_date = update_data.get(
        "delivery_date",
        _coerce_order_date(doc.get("delivery_date")),
    )
    effective_items = update_data.get("items", doc.get("items", []))
    _validate_sales_order_payload(
        effective_transaction_date,
        effective_delivery_date,
        effective_items,
    )

    if "items" in update_data:
        items_raw = update_data["items"]
        items_raw, total = calculate_line_totals(items_raw)
        update_data["items"] = items_raw
        update_data["total"] = total
        update_data["grand_total"] = total
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "판매주문이 수정되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("sales_order:submit"))])
def submit_sales_order(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """판매주문을 제출한다 (초안 → 제출)."""
    repo = _get_repo(user.tenant_id)
    submit_document(repo, doc_id, _NOT_FOUND)

    repo.submit_with_event(
        doc_id,
        event_type=EventType.SALES_ORDER_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return {"id": doc_id, "message": "판매주문이 제출되었습니다"}


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("sales_order:cancel"))])
def cancel_sales_order(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """판매주문을 취소한다 (제출 → 취소)."""
    repo = _get_repo(user.tenant_id)
    cancel_document(repo, doc_id, _NOT_FOUND)
    return {"id": doc_id, "message": "판매주문이 취소되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("sales_order:delete"))]
)
def delete_sales_order(doc_id: str, user: CurrentUserDep) -> None:
    """판매주문을 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    delete_draft(repo, doc_id, _NOT_FOUND)


@router.post(
    "/{doc_id}/delivery-note",
    status_code=201,
    dependencies=[Depends(require_permission("delivery_note:create"))],
)
def create_delivery_note_from_sales_order(
    doc_id: str,
    body: SalesOrderDeliveryNoteCreate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """제출된 판매주문에서 납품서 초안을 생성한다."""
    repo = _get_repo(user.tenant_id)
    sales_order = get_or_404(repo, doc_id, _NOT_FOUND)
    _require_submitted_sales_order(sales_order, "납품서")

    posting_date = (
        body.posting_date
        or _coerce_order_date(sales_order.get("delivery_date"))
        or _coerce_order_date(sales_order.get("transaction_date"))
        or datetime.now(tz=UTC).date()
    )
    items = [
        DeliveryNoteItem(
            item_code=item.get("item_code", ""),
            item_name=item.get("item_name", ""),
            qty=item.get("qty", 0),
            rate=item.get("rate", 0),
            amount=item.get("amount", 0),
            warehouse=body.warehouse or item.get("warehouse", ""),
            batch_no=item.get("batch_no"),
        )
        for item in sales_order.get("items", [])
    ]

    delivery_note_id = generate_name(_DELIVERY_NOTE_PREFIX, tenant_id=user.tenant_id)
    delivery_note = DeliveryNote(
        _id=delivery_note_id,
        tenant_id=user.tenant_id,
        customer_id=sales_order.get("customer_id", ""),
        customer_name=sales_order.get("customer_name", ""),
        sales_partner_id=sales_order.get("sales_partner_id", ""),
        sales_partner_name=sales_order.get("sales_partner_name", ""),
        sales_partner_commission_rate=sales_order.get("sales_partner_commission_rate", 0),
        posting_date=posting_date,
        sales_order_ref=doc_id,
        items=items,
        transporter=body.transporter,
        created_by=user.sub,
        updated_by=user.sub,
    )
    _get_delivery_note_repo(user.tenant_id).insert(delivery_note)

    downstream_refs = _append_downstream_ref(
        sales_order.get("downstream_refs", {}),
        "delivery_note_ids",
        delivery_note_id,
    )
    repo.update_by_id(doc_id, {"downstream_refs": downstream_refs})

    return {
        "id": delivery_note_id,
        "sales_order_ref": doc_id,
        "message": "판매주문에서 납품서 초안을 생성했습니다",
        "downstream_summary": _build_downstream_summary(downstream_refs),
    }


@router.post(
    "/{doc_id}/sales-invoice",
    status_code=201,
    dependencies=[Depends(require_permission("sales_invoice:create"))],
)
def create_sales_invoice_from_sales_order(
    doc_id: str,
    body: SalesOrderInvoiceCreate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """제출된 판매주문에서 판매송장 초안을 생성한다."""
    repo = _get_repo(user.tenant_id)
    sales_order = get_or_404(repo, doc_id, _NOT_FOUND)
    _require_submitted_sales_order(sales_order, "판매송장")

    posting_date = (
        body.posting_date
        or _coerce_order_date(sales_order.get("delivery_date"))
        or _coerce_order_date(sales_order.get("transaction_date"))
        or datetime.now(tz=UTC).date()
    )
    due_date = body.due_date or posting_date

    items_raw = [
        {
            "item_code": item.get("item_code", ""),
            "item_name": item.get("item_name", ""),
            "qty": item.get("qty", 0),
            "rate": item.get("rate", 0),
            "amount": item.get("amount", 0),
        }
        for item in sales_order.get("items", [])
    ]
    taxes_raw = [
        {
            "tax_type": tax.tax_type,
            "rate": float(tax.rate),
            "amount": float(tax.amount),
        }
        for tax in body.taxes
    ]
    grand_total = calculate_line_totals_with_taxes(items_raw, taxes_raw)
    net_total = sum(item.get("amount", 0) for item in items_raw)

    sales_invoice_id = generate_name(_SALES_INVOICE_PREFIX, tenant_id=user.tenant_id)
    sales_invoice = SalesInvoice(
        _id=sales_invoice_id,
        tenant_id=user.tenant_id,
        customer_id=sales_order.get("customer_id", ""),
        customer_name=sales_order.get("customer_name", ""),
        sales_partner_id=sales_order.get("sales_partner_id", ""),
        sales_partner_name=sales_order.get("sales_partner_name", ""),
        sales_partner_commission_rate=sales_order.get("sales_partner_commission_rate", 0),
        posting_date=posting_date,
        due_date=due_date,
        sales_order_ref=doc_id,
        items=[SalesInvoiceItem(**item) for item in items_raw],
        taxes=_normalize_sales_invoice_taxes(taxes_raw),
        net_total=net_total,
        grand_total=grand_total,
        outstanding_amount=grand_total,
        etax_invoice_ref=body.etax_invoice_ref,
        created_by=user.sub,
        updated_by=user.sub,
    )
    _get_sales_invoice_repo(user.tenant_id).insert(sales_invoice)

    downstream_refs = _append_downstream_ref(
        sales_order.get("downstream_refs", {}),
        "sales_invoice_ids",
        sales_invoice_id,
    )
    repo.update_by_id(doc_id, {"downstream_refs": downstream_refs})

    return {
        "id": sales_invoice_id,
        "sales_order_ref": doc_id,
        "message": "판매주문에서 판매송장 초안을 생성했습니다",
        "downstream_summary": _build_downstream_summary(downstream_refs),
    }
