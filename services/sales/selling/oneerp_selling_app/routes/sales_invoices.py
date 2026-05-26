"""매출송장(Sales Invoice) 커스텀 라우터."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request
from oneerp_core.events.schemas import EventType
from oneerp_core.line_items import calculate_line_totals_with_taxes
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.route_helpers import check_draft_status, delete_draft, get_or_404, submit_document

from oneerp_selling_app.dto import SalesInvoiceCreate, SalesInvoiceUpdate
from oneerp_selling_app.models.sales_invoice import SalesInvoice
from oneerp_selling_app.services.sales_invoice_repo_service import SalesInvoiceRepoService
from oneerp_selling_app.services.sales_partner_snapshot import resolve_sales_partner_snapshot

router = APIRouter(prefix="/api/v1/sales-invoices", tags=["판매송장"])

_COLLECTION = "sales_invoices"
_ETAX_COLLECTION = "etax_invoices"
_PREFIX = "SINV"
_ETAX_PREFIX = "ETAX"
_NOT_FOUND = "판매송장을 찾을 수 없습니다"
_REPORT_COMPANY = {
    "name": "원이알피 주식회사",
    "ceo": "김대표",
    "address": "서울특별시 강남구 테헤란로 123",
    "businessNumber": "123-45-67890",
    "phone": "02-1234-5678",
}


def _get_repo(tenant_id: str):  # type: ignore[no-untyped-def]
    """판매송장 Repository — Route→Service 은닉 후 호환 shim."""
    return SalesInvoiceRepoService(tenant_id).invoices


def _get_etax_repo(tenant_id: str):  # type: ignore[no-untyped-def]
    """전자세금계산서 Repository — Route→Service 은닉 후 호환 shim."""
    return SalesInvoiceRepoService(tenant_id).etax_invoices


def _to_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _to_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _build_payment_summary(doc: dict[str, Any]) -> dict[str, Any]:
    grand_total = _to_decimal(doc.get("grand_total", 0))
    outstanding_amount = _to_decimal(doc.get("outstanding_amount", grand_total))
    collected_amount = max(grand_total - outstanding_amount, Decimal(0))
    return {
        "grand_total": float(grand_total),
        "outstanding_amount": float(outstanding_amount),
        "collected_amount": float(collected_amount),
        "is_paid_in_full": outstanding_amount <= 0,
    }


def _resolve_status_badge(doc: dict[str, Any]) -> str:
    docstatus = doc.get("docstatus", 0)
    if docstatus in {DocStatus.CANCELLED, 2, "cancelled", "Cancelled"}:
        return "cancelled"
    if docstatus in {DocStatus.SUBMITTED, 1, "submitted", "Submitted"}:
        payment_summary = _build_payment_summary(doc)
        if payment_summary["is_paid_in_full"]:
            return "submitted_paid"
        if payment_summary["collected_amount"] > 0:
            return "submitted_partial"
        return "submitted_unpaid"
    return "draft"


def _build_etax_summary(doc: dict[str, Any], *, tenant_id: str) -> dict[str, Any]:
    etax_invoice_id = doc.get("etax_invoice_ref")
    if not etax_invoice_id:
        return {
            "etax_invoice_id": None,
            "transmission_status": "not_requested",
            "nts_confirmation_no": None,
        }

    etax_doc = _get_etax_repo(tenant_id).find_by_id(str(etax_invoice_id))
    if not etax_doc:
        return {
            "etax_invoice_id": etax_invoice_id,
            "transmission_status": "missing",
            "nts_confirmation_no": None,
        }
    return {
        "etax_invoice_id": etax_doc.get("_id", etax_invoice_id),
        "transmission_status": etax_doc.get("transmission_status", "pending"),
        "nts_confirmation_no": etax_doc.get("nts_confirmation_no"),
    }


def _build_available_actions(
    *,
    status_badge: str,
    etax_summary: dict[str, Any],
) -> list[str]:
    if status_badge == "draft":
        return ["submit", "edit", "delete"]
    if status_badge.startswith("submitted"):
        actions = ["register_payment", "open_accounts_receivable"]
        if etax_summary.get("etax_invoice_id"):
            actions.append("open_etax_invoice")
        if etax_summary.get("transmission_status") == "pending":
            actions.append("submit_etax_to_nts")
        actions.append("cancel")
        return actions
    return []


def _serialize_invoice(doc: dict[str, Any], *, tenant_id: str) -> dict[str, Any]:
    payload = dict(doc)
    payload["id"] = payload.get("_id", payload.get("id"))
    payload["payment_summary"] = _build_payment_summary(payload)
    payload["status_badge"] = _resolve_status_badge(payload)
    payload["etax_summary"] = _build_etax_summary(payload, tenant_id=tenant_id)
    payload["available_actions"] = _build_available_actions(
        status_badge=payload["status_badge"],
        etax_summary=payload["etax_summary"],
    )
    return payload


def _matches_filters(
    doc: dict[str, Any],
    *,
    status_badge: str | None,
    transmission_status: str | None,
) -> bool:
    if status_badge and doc.get("status_badge") != status_badge:
        return False
    return not (
        transmission_status
        and doc.get("etax_summary", {}).get("transmission_status") != transmission_status
    )


def _ensure_etax_invoice_ref(doc_id: str, doc: dict[str, Any], user: CurrentUserDep) -> str:
    etax_ref = str(doc.get("etax_invoice_ref") or "").strip()
    if etax_ref:
        return etax_ref

    grand_total = _to_decimal(doc.get("grand_total", 0))
    net_total = _to_decimal(doc.get("net_total", 0))
    etax_id = generate_name(_ETAX_PREFIX, tenant_id=user.tenant_id)
    _get_etax_repo(user.tenant_id).insert(
        {
            "_id": etax_id,
            "tenant_id": user.tenant_id,
            "invoice_ref": doc_id,
            "issue_date": (
                _to_date(doc.get("posting_date")) or datetime.now(tz=UTC).date()
            ).isoformat(),
            "supplier_or_customer": doc.get("customer_name") or doc.get("customer_id", ""),
            "supply_amount": float(net_total),
            "tax_amount": float(grand_total - net_total),
            "transmission_status": "pending",
            "created_by": user.sub,
            "updated_by": user.sub,
        }
    )
    return etax_id


def _resolve_vat_rate(doc: dict[str, Any]) -> float:
    taxes = doc.get("taxes", [])
    if isinstance(taxes, list) and taxes:
        rate = float(taxes[0].get("rate", 0.1))
        return rate / 100 if rate > 1 else rate
    return 0.1


def _build_sales_invoice_report(doc: dict[str, Any]) -> dict[str, Any]:
    """PDF 렌더링용 판매송장 정규화 응답을 구성한다."""
    posting_date = _to_date(doc.get("posting_date")) or datetime.now(tz=UTC).date()
    return {
        "invoice_number": doc.get("_id") or doc.get("id", ""),
        "invoice_date": posting_date.isoformat(),
        "customer": {
            "name": doc.get("customer_name") or doc.get("customer_id", ""),
            "business_number": doc.get("customer_business_number") or doc.get("business_number"),
            "contact_name": doc.get("customer_contact_name") or doc.get("contact_name"),
            "address": doc.get("customer_address") or doc.get("billing_address"),
        },
        "items": [
            {
                "item_name": item.get("item_name") or item.get("item_code", ""),
                "spec": item.get("spec") or item.get("description"),
                "quantity": float(item.get("qty", item.get("quantity", 0)) or 0),
                "unit": item.get("unit") or item.get("uom"),
                "unit_price": float(item.get("rate", item.get("unit_price", 0)) or 0),
            }
            for item in doc.get("items", [])
        ],
        "vat_rate": _resolve_vat_rate(doc),
        "company": {
            "name": doc.get("company_name") or _REPORT_COMPANY["name"],
            "ceo": doc.get("company_ceo") or _REPORT_COMPANY["ceo"],
            "address": doc.get("company_address") or _REPORT_COMPANY["address"],
            "businessNumber": doc.get("company_business_number")
            or _REPORT_COMPANY["businessNumber"],
            "phone": doc.get("company_phone") or _REPORT_COMPANY["phone"],
        },
        "remark": doc.get("remark", ""),
    }


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(require_permission("sales_invoice:create"))],
)
def 판매송장_생성(body: SalesInvoiceCreate, user: CurrentUserDep) -> dict[str, Any]:
    """판매송장을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    items_raw = [item.model_dump() for item in body.items]
    taxes_raw = [tax.model_dump() for tax in body.taxes]
    grand_total = calculate_line_totals_with_taxes(items_raw, taxes_raw)
    net_total = sum(item.get("amount", 0) for item in items_raw)

    invoice = SalesInvoice(
        _id=doc_id,
        tenant_id=user.tenant_id,
        customer_id=body.customer_id,
        customer_name=body.customer_name,
        **resolve_sales_partner_snapshot(user.tenant_id, body.customer_id),
        posting_date=body.posting_date,
        due_date=body.due_date,
        sales_order_ref=body.sales_order_ref,
        delivery_note_ref=body.delivery_note_ref,
        items=body.items,
        taxes=body.taxes,
        net_total=net_total,
        grand_total=grand_total,
        outstanding_amount=grand_total,
        etax_invoice_ref=body.etax_invoice_ref,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(invoice)

    return {"id": doc_id, "message": "판매송장이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("sales_invoice:read"))])
def 판매송장_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    customer_id: str | None = None,
    sales_order_ref: str | None = None,
    delivery_note_ref: str | None = None,
    status_badge: str | None = None,
    transmission_status: str | None = None,
) -> dict[str, Any]:
    """판매송장 목록을 상태/전자세금계산서 맥락과 함께 조회한다."""
    repo = _get_repo(user.tenant_id)
    filter_query: dict[str, Any] = {}
    if customer_id:
        filter_query["customer_id"] = customer_id
    if sales_order_ref:
        filter_query["sales_order_ref"] = sales_order_ref
    if delivery_note_ref:
        filter_query["delivery_note_ref"] = delivery_note_ref

    docs = [
        _serialize_invoice(doc, tenant_id=user.tenant_id)
        for doc in list(repo.find_many(filter_query, sort=[("created_at", -1)]))
    ]
    filtered = [
        doc
        for doc in docs
        if _matches_filters(
            doc,
            status_badge=status_badge,
            transmission_status=transmission_status,
        )
    ]
    start = max(page - 1, 0) * page_size
    end = start + page_size
    return {
        "data": filtered[start:end],
        "total": len(filtered),
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}/report", dependencies=[Depends(require_permission("sales_invoice:read"))])
def 판매송장_리포트_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """PDF 렌더링용 판매송장 정규화 데이터를 반환한다."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    return _build_sales_invoice_report(doc)


@router.get("/{doc_id}", dependencies=[Depends(require_permission("sales_invoice:read"))])
def 판매송장_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """판매송장 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    return _serialize_invoice(get_or_404(repo, doc_id, _NOT_FOUND), tenant_id=user.tenant_id)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("sales_invoice:write"))])
def 판매송장_수정(
    doc_id: str,
    body: SalesInvoiceUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """판매송장을 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    check_draft_status(doc, "수정")

    update_data = body.model_dump(exclude_none=True)
    if "items" in update_data or "taxes" in update_data:
        items_raw = update_data.get("items", [item.model_dump() for item in body.items or []])
        taxes_raw = update_data.get("taxes", [tax.model_dump() for tax in body.taxes or []])
        grand_total = calculate_line_totals_with_taxes(items_raw, taxes_raw)
        update_data["items"] = items_raw
        update_data["taxes"] = taxes_raw
        update_data["net_total"] = sum(item.get("amount", 0) for item in items_raw)
        update_data["grand_total"] = grand_total
        update_data["outstanding_amount"] = grand_total
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "판매송장이 수정되었습니다"}


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("sales_invoice:submit"))])
def 판매송장_제출(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """판매송장을 제출하고 전자세금계산서 초안을 자동 연결한다."""
    repo = _get_repo(user.tenant_id)
    doc = submit_document(repo, doc_id, _NOT_FOUND)

    grand_total = _to_decimal(doc.get("grand_total", 0))
    etax_invoice_ref = ""
    if grand_total > 0:
        etax_invoice_ref = _ensure_etax_invoice_ref(doc_id, doc, user)
    update_data: dict[str, Any] = {"outstanding_amount": float(grand_total)}
    if etax_invoice_ref or doc.get("etax_invoice_ref"):
        update_data["etax_invoice_ref"] = etax_invoice_ref or doc.get("etax_invoice_ref")
    repo.update_by_id(doc_id, update_data)

    repo.submit_with_event(
        doc_id,
        event_type=EventType.SALES_INVOICE_SUBMITTED,
        event_data={
            "doc_id": doc_id,
            "grand_total": float(grand_total),
            "net_total": float(_to_decimal(doc.get("net_total", 0))),
            "customer": doc.get("customer_id", ""),
            "customer_name": doc.get("customer_name", ""),
            "posting_date": str(doc.get("posting_date", "")),
            "due_date": str(doc.get("due_date", "")),
            "etax_invoice_ref": etax_invoice_ref,
        },
        triggered_by=user.sub,
    )
    return _serialize_invoice(get_or_404(repo, doc_id, _NOT_FOUND), tenant_id=user.tenant_id)


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("sales_invoice:cancel"))])
def 판매송장_취소(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """판매송장을 취소한다."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request("제출된 문서만 취소할 수 있습니다")
    repo.cancel(doc_id)
    return _serialize_invoice(get_or_404(repo, doc_id, _NOT_FOUND), tenant_id=user.tenant_id)


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("sales_invoice:delete"))],
)
def 판매송장_삭제(doc_id: str, user: CurrentUserDep) -> None:
    """판매송장을 삭제한다. 초안 상태에서만 허용한다."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    check_draft_status(doc, "삭제")
    delete_draft(repo, doc_id, _NOT_FOUND)
