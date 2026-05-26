"""납품서(Delivery Note) 커스텀 라우터."""

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

from oneerp_selling_app.dto import DeliveryNoteCreate, DeliveryNoteUpdate
from oneerp_selling_app.models.delivery_note import DeliveryNote, DeliveryNoteItem
from oneerp_selling_app.models.sales_invoice import SalesInvoice, SalesInvoiceItem, SalesInvoiceTax
from oneerp_selling_app.services.delivery_note_service import DeliveryNoteRepoService
from oneerp_selling_app.services.sales_partner_snapshot import resolve_sales_partner_snapshot

router = APIRouter(prefix="/api/v1/delivery-notes", tags=["납품서"])

_PREFIX = "DN"
_SALES_INVOICE_PREFIX = "SINV"
_NOT_FOUND = "납품서를 찾을 수 없습니다"


def _get_repo(tenant_id: str):  # type: ignore[no-untyped-def]
    """납품서 Repository — Route→Service 은닉 후 호환 shim."""
    return DeliveryNoteRepoService(tenant_id).notes


def _get_sales_invoice_repo(tenant_id: str):  # type: ignore[no-untyped-def]
    """판매송장 Repository — Route→Service 은닉 후 호환 shim."""
    return DeliveryNoteRepoService(tenant_id).invoices


class DeliveryNoteInvoiceCreate(BaseModel):
    """납품서 기준 판매송장 초안 생성 입력."""

    posting_date: date | None = None
    due_date: date | None = None
    taxes: list[SalesInvoiceTax] = []
    etax_invoice_ref: str | None = None


def _normalize_downstream_refs(value: Any) -> dict[str, list[str]]:
    refs = value if isinstance(value, dict) else {}
    return {"sales_invoice_ids": list(refs.get("sales_invoice_ids") or [])}


def _build_downstream_summary(refs: dict[str, list[str]]) -> dict[str, Any]:
    sales_invoice_count = len(refs["sales_invoice_ids"])
    return {
        "sales_invoice_count": sales_invoice_count,
        "has_downstream_documents": sales_invoice_count > 0,
    }


def _status_badge(docstatus: Any) -> str:
    if docstatus in {DocStatus.SUBMITTED, 1, "submitted", "Submitted"}:
        return "submitted"
    if docstatus in {DocStatus.CANCELLED, 2, "cancelled", "Cancelled"}:
        return "cancelled"
    return "draft"


def _available_actions(status_badge: str) -> list[str]:
    if status_badge == "draft":
        return ["submit", "edit", "delete"]
    if status_badge == "submitted":
        return ["create_sales_invoice", "cancel"]
    return []


def _build_delivery_note_response(doc: dict[str, Any]) -> dict[str, Any]:
    payload = dict(doc)
    refs = _normalize_downstream_refs(payload.get("downstream_refs"))
    badge = _status_badge(payload.get("docstatus"))
    payload["id"] = payload.get("_id", payload.get("id"))
    payload["downstream_refs"] = refs
    payload["status_badge"] = badge
    payload["downstream_summary"] = _build_downstream_summary(refs)
    payload["available_actions"] = _available_actions(badge)
    return payload


def _build_filter_query(
    *,
    customer_id: str | None,
    sales_order_ref: str | None,
    transporter: str | None,
    status_badge: str | None,
) -> dict[str, Any]:
    query: dict[str, Any] = {}
    if customer_id:
        query["customer_id"] = customer_id
    if sales_order_ref:
        query["sales_order_ref"] = sales_order_ref
    if transporter:
        query["transporter"] = transporter
    if status_badge == "draft":
        query["docstatus"] = DocStatus.DRAFT
    elif status_badge == "submitted":
        query["docstatus"] = DocStatus.SUBMITTED
    elif status_badge == "cancelled":
        query["docstatus"] = DocStatus.CANCELLED
    return query


def _coerce_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    return None


def _normalize_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not items:
        raise_bad_request("ERR-SELL-049: 납품서 품목은 1건 이상이어야 합니다")
    normalized_items, _ = calculate_line_totals(items)
    return normalized_items


def _ensure_ready_to_submit(doc: dict[str, Any]) -> None:
    items = list(doc.get("items") or [])
    _normalize_items(items)
    for item in items:
        if not str(item.get("warehouse", "")).strip():
            raise_bad_request(
                "ERR-SELL-050: 제출 전에 모든 납품 품목에 출고 창고를 지정해야 합니다"
            )


def _append_invoice_ref(refs: Any, invoice_id: str) -> dict[str, list[str]]:
    normalized = _normalize_downstream_refs(refs)
    if invoice_id not in normalized["sales_invoice_ids"]:
        normalized["sales_invoice_ids"].append(invoice_id)
    return normalized


def _normalize_sales_invoice_taxes(taxes: list[dict[str, Any]]) -> list[SalesInvoiceTax]:
    return [
        SalesInvoiceTax(
            tax_type=str(tax.get("tax_type", "") or ""),
            rate=Decimal(str(tax.get("rate", 0) or 0)),
            amount=Decimal(str(tax.get("amount", 0) or 0)),
        )
        for tax in taxes
    ]


def _build_invoice_items(delivery_note: dict[str, Any]) -> list[dict[str, Any]]:
    items_raw = _normalize_items(
        [
            {
                "item_code": item.get("item_code", ""),
                "item_name": item.get("item_name", item.get("item_code", "")),
                "qty": item.get("qty", 0),
                "rate": item.get("rate", 0),
                "amount": item.get("amount", 0),
            }
            for item in delivery_note.get("items", [])
        ]
    )
    if any(float(item.get("rate", 0) or 0) <= 0 for item in items_raw):
        raise_bad_request("단가가 없는 납품서는 판매송장으로 전환할 수 없습니다")
    return items_raw


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("delivery_note:create"))]
)
def create_delivery_note(body: DeliveryNoteCreate, user: CurrentUserDep) -> dict[str, Any]:
    """납품서를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    items_raw = _normalize_items([item.model_dump() for item in body.items])
    delivery_note = DeliveryNote(
        _id=doc_id,
        tenant_id=user.tenant_id,
        customer_id=body.customer_id,
        customer_name=body.customer_name,
        **resolve_sales_partner_snapshot(user.tenant_id, body.customer_id),
        posting_date=body.posting_date,
        sales_order_ref=body.sales_order_ref,
        items=[DeliveryNoteItem(**item) for item in items_raw],
        transporter=body.transporter,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(delivery_note)
    return {"id": doc_id, "message": "납품서가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("delivery_note:read"))])
def list_delivery_notes(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    customer_id: str | None = None,
    sales_order_ref: str | None = None,
    transporter: str | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    payload = paginated_list(
        repo,
        page,
        page_size,
        filter_query=_build_filter_query(
            customer_id=customer_id,
            sales_order_ref=sales_order_ref,
            transporter=transporter,
            status_badge=status_badge,
        ),
    )
    payload["data"] = [_build_delivery_note_response(doc) for doc in payload["data"]]
    return payload


@router.get("/{doc_id}", dependencies=[Depends(require_permission("delivery_note:read"))])
def get_delivery_note(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    return _build_delivery_note_response(get_or_404(repo, doc_id, _NOT_FOUND))


@router.put("/{doc_id}", dependencies=[Depends(require_permission("delivery_note:write"))])
def update_delivery_note(
    doc_id: str, body: DeliveryNoteUpdate, user: CurrentUserDep
) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    check_draft_status(doc, "수정")

    update_data = body.model_dump(exclude_none=True)
    if "items" in update_data:
        items_raw = _normalize_items(update_data["items"])
        update_data["items"] = items_raw
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "납품서가 수정되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("delivery_note:submit"))])
def submit_delivery_note(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    doc = submit_document(repo, doc_id, _NOT_FOUND)
    _ensure_ready_to_submit(doc)
    repo.submit_with_event(
        doc_id,
        event_type=EventType.DELIVERY_NOTE_SUBMITTED,
        event_data={"doc_id": doc_id},
        triggered_by=user.sub,
    )
    return _build_delivery_note_response(get_or_404(repo, doc_id, _NOT_FOUND))


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("delivery_note:cancel"))])
def cancel_delivery_note(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    cancel_document(repo, doc_id, _NOT_FOUND)
    return _build_delivery_note_response(get_or_404(repo, doc_id, _NOT_FOUND))


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("delivery_note:delete"))],
)
def delete_delivery_note(doc_id: str, user: CurrentUserDep) -> None:
    repo = _get_repo(user.tenant_id)
    delete_draft(repo, doc_id, _NOT_FOUND)


@router.post(
    "/{doc_id}/sales-invoice",
    status_code=201,
    dependencies=[Depends(require_permission("sales_invoice:create"))],
)
def create_sales_invoice_from_delivery_note(
    doc_id: str,
    body: DeliveryNoteInvoiceCreate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """제출된 납품서에서 판매송장 초안을 생성한다."""
    delivery_repo = _get_repo(user.tenant_id)
    delivery_note = get_or_404(delivery_repo, doc_id, _NOT_FOUND)
    if delivery_note.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request("제출된 납품서에서만 판매송장을 생성할 수 있습니다")

    posting_date = (
        body.posting_date
        or _coerce_date(delivery_note.get("posting_date"))
        or datetime.now(tz=UTC).date()
    )
    due_date = body.due_date or posting_date
    items_raw = _build_invoice_items(delivery_note)
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
        customer_id=delivery_note.get("customer_id", ""),
        customer_name=delivery_note.get("customer_name", ""),
        sales_partner_id=delivery_note.get("sales_partner_id", ""),
        sales_partner_name=delivery_note.get("sales_partner_name", ""),
        sales_partner_commission_rate=delivery_note.get("sales_partner_commission_rate", 0),
        posting_date=posting_date,
        due_date=due_date,
        sales_order_ref=delivery_note.get("sales_order_ref"),
        delivery_note_ref=doc_id,
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

    downstream_refs = _append_invoice_ref(delivery_note.get("downstream_refs"), sales_invoice_id)
    delivery_repo.update_by_id(
        doc_id,
        {
            "downstream_refs": downstream_refs,
            "updated_by": user.sub,
        },
    )
    return {
        "id": sales_invoice_id,
        "delivery_note_ref": doc_id,
        "message": "납품서에서 판매송장 초안을 생성했습니다",
        "downstream_summary": _build_downstream_summary(downstream_refs),
    }
