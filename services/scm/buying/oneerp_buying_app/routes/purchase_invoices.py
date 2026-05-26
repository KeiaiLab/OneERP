"""구매송장(Purchase Invoice) 워크벤치 라우터."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.events.schemas import EventType
from oneerp_core.line_items import calculate_line_totals_with_taxes
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_buying_app.models.purchase_invoice import (
    PurchaseInvoice,
    PurchaseInvoiceCreate,
    PurchaseInvoiceUpdate,
)

router = APIRouter(prefix="/api/v1/purchase-invoices", tags=["구매송장"])

_COLLECTION = "purchase_invoices"
_PREFIX = "PI"
_ETAX_COLLECTION = "etax_invoices"
_ETAX_PREFIX = "ETAX"
_MATCH_TOLERANCE = Decimal("0.0001")
_NOT_FOUND = "구매송장을 찾을 수 없습니다"


def _get_repo(tenant_id: str) -> Repository:
    """구매송장 저장소를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_etax_repo(tenant_id: str) -> Repository:
    """전자세금계산서 저장소를 반환한다."""
    return Repository(_ETAX_COLLECTION, tenant_id=tenant_id)


def _get_purchase_order_repo(tenant_id: str) -> Repository:
    """구매주문 저장소를 반환한다."""
    return Repository("purchase_orders", tenant_id=tenant_id)


def _get_purchase_receipt_repo(tenant_id: str) -> Repository:
    """구매입고 저장소를 반환한다."""
    return Repository("purchase_receipts", tenant_id=tenant_id)


def _to_decimal(value: Any) -> Decimal:
    """숫자/문자열을 Decimal로 정규화한다."""
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _to_date(value: Any) -> date | None:
    """문자열/날짜를 date로 정규화한다."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _sum_item_qty(items: list[dict[str, Any]]) -> Decimal:
    """라인 수량 합계를 계산한다."""
    return sum((_to_decimal(item.get("qty", 0)) for item in items), Decimal(0))


def _sum_item_amount(items: list[dict[str, Any]]) -> Decimal:
    """라인 금액 합계를 계산한다."""
    return sum((_to_decimal(item.get("amount", 0)) for item in items), Decimal(0))


def _sum_tax_amount(taxes: list[dict[str, Any]]) -> Decimal:
    """세금 금액 합계를 계산한다."""
    return sum((_to_decimal(tax.get("amount", 0)) for tax in taxes), Decimal(0))


def _resolve_net_total(doc: dict[str, Any]) -> Decimal:
    """저장된 net_total 또는 라인 금액 합계를 반환한다."""
    return _to_decimal(doc.get("net_total", _sum_item_amount(doc.get("items", []))))


def _resolve_grand_total(doc: dict[str, Any]) -> Decimal:
    """저장된 grand_total 또는 세전/세액 합계를 반환한다."""
    default_total = _resolve_net_total(doc) + _sum_tax_amount(doc.get("taxes", []))
    return _to_decimal(doc.get("grand_total", default_total))


def _build_payment_summary(doc: dict[str, Any]) -> dict[str, Any]:
    """지급 요약을 계산한다."""
    grand_total = _resolve_grand_total(doc)
    outstanding_amount = _to_decimal(doc.get("outstanding_amount", grand_total))
    paid_amount = max(grand_total - outstanding_amount, Decimal(0))
    return {
        "grand_total": float(grand_total),
        "outstanding_amount": float(outstanding_amount),
        "paid_amount": float(paid_amount),
        "is_paid_in_full": outstanding_amount <= 0,
    }


def _resolve_status_badge(doc: dict[str, Any]) -> str:
    """구매송장 상태 배지를 계산한다."""
    docstatus = int(doc.get("docstatus", 0) or 0)
    if docstatus == DocStatus.DRAFT:
        return "draft"
    if docstatus == DocStatus.CANCELLED:
        return "cancelled"

    payment_summary = _build_payment_summary(doc)
    if payment_summary["is_paid_in_full"]:
        return "settled"
    if payment_summary["paid_amount"] > 0:
        return "submitted_partial"
    return "submitted_unpaid"


def _build_etax_summary(doc: dict[str, Any], *, tenant_id: str) -> dict[str, Any]:
    """전자세금계산서 연계 상태를 반환한다."""
    etax_invoice_id = str(doc.get("etax_invoice_ref") or "").strip()
    if not etax_invoice_id:
        return {
            "etax_invoice_id": None,
            "transmission_status": "not_requested",
            "nts_confirmation_no": None,
        }

    etax_doc = _get_etax_repo(tenant_id).find_by_id(etax_invoice_id)
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


def _calculate_reference_summary(reference_doc: dict[str, Any] | None) -> tuple[Decimal, Decimal]:
    """참조 문서의 수량/금액 합계를 계산한다."""
    if not reference_doc:
        return Decimal(0), Decimal(0)
    items = reference_doc.get("items", [])
    return _sum_item_qty(items), _sum_item_amount(items)


def _build_matching_summary(doc: dict[str, Any], *, tenant_id: str) -> dict[str, Any]:
    """구매주문/입고 기준 3-way 매칭 요약을 계산한다."""
    purchase_order_id = str(doc.get("purchase_order_id") or "").strip() or None
    purchase_receipt_id = str(doc.get("purchase_receipt_id") or "").strip() or None
    invoice_qty = _sum_item_qty(doc.get("items", []))
    invoice_amount = _resolve_net_total(doc)

    comparison_basis: str | None = None
    match_status = "manual_entry"
    reference_qty: Decimal | None = None
    reference_amount: Decimal | None = None

    if purchase_receipt_id:
        comparison_basis = "purchase_receipt"
        receipt_doc = _get_purchase_receipt_repo(tenant_id).find_by_id(purchase_receipt_id)
        if receipt_doc:
            reference_qty, reference_amount = _calculate_reference_summary(receipt_doc)
            qty_delta = invoice_qty - reference_qty
            amount_delta = invoice_amount - reference_amount
            match_status = (
                "matched"
                if abs(qty_delta) <= _MATCH_TOLERANCE and abs(amount_delta) <= _MATCH_TOLERANCE
                else "variance"
            )
        else:
            match_status = "reference_missing"
    elif purchase_order_id:
        comparison_basis = "purchase_order"
        purchase_order_doc = _get_purchase_order_repo(tenant_id).find_by_id(purchase_order_id)
        if purchase_order_doc:
            reference_qty, reference_amount = _calculate_reference_summary(purchase_order_doc)
            qty_delta = invoice_qty - reference_qty
            amount_delta = invoice_amount - reference_amount
            match_status = (
                "matched"
                if abs(qty_delta) <= _MATCH_TOLERANCE and abs(amount_delta) <= _MATCH_TOLERANCE
                else "variance"
            )
        else:
            match_status = "reference_missing"

    qty_delta = invoice_qty - reference_qty if reference_qty is not None else Decimal(0)
    amount_delta = invoice_amount - reference_amount if reference_amount is not None else Decimal(0)
    return {
        "match_status": match_status,
        "comparison_basis": comparison_basis or "manual_entry",
        "purchase_order_id": purchase_order_id,
        "purchase_receipt_id": purchase_receipt_id,
        "invoice_qty": float(invoice_qty),
        "reference_qty": float(reference_qty) if reference_qty is not None else None,
        "qty_delta": float(qty_delta) if reference_qty is not None else None,
        "invoice_amount": float(invoice_amount),
        "reference_amount": float(reference_amount) if reference_amount is not None else None,
        "amount_delta": float(amount_delta) if reference_amount is not None else None,
    }


def _build_available_actions(
    *,
    doc: dict[str, Any],
    status_badge: str,
    etax_summary: dict[str, Any],
) -> list[str]:
    """상태 기반 다음 액션을 계산한다."""
    purchase_order_id = str(doc.get("purchase_order_id") or "").strip()
    purchase_receipt_id = str(doc.get("purchase_receipt_id") or "").strip()

    if status_badge == "draft":
        actions = ["submit", "edit", "delete"]
    elif status_badge == "cancelled":
        actions = []
    else:
        actions = ["open_accounts_payable"]
        if status_badge != "settled":
            actions.insert(0, "register_payment")

    if purchase_order_id:
        actions.append("open_purchase_order")
    if purchase_receipt_id:
        actions.append("open_purchase_receipt")
    if status_badge not in {"draft", "cancelled"}:
        if etax_summary.get("etax_invoice_id"):
            actions.append("open_etax_invoice")
        if etax_summary.get("transmission_status") == "pending":
            actions.append("submit_etax_to_nts")
        actions.append("cancel")
    return actions


def _serialize_invoice(doc: dict[str, Any], *, tenant_id: str) -> dict[str, Any]:
    """목록/상세 응답에 운영 요약을 추가한다."""
    payload = dict(doc)
    payload["id"] = payload.get("_id", payload.get("id"))
    payload["payment_summary"] = _build_payment_summary(payload)
    payload["status_badge"] = _resolve_status_badge(payload)
    payload["etax_summary"] = _build_etax_summary(payload, tenant_id=tenant_id)
    payload["matching_summary"] = _build_matching_summary(payload, tenant_id=tenant_id)
    payload["available_actions"] = _build_available_actions(
        doc=payload,
        status_badge=payload["status_badge"],
        etax_summary=payload["etax_summary"],
    )
    return payload


def _matches_filters(
    doc: dict[str, Any],
    *,
    supplier_id: str | None,
    purchase_order_id: str | None,
    purchase_receipt_id: str | None,
    status_badge: str | None,
    transmission_status: str | None,
    match_status: str | None,
) -> bool:
    """목록 필터 조건을 평가한다."""
    if supplier_id and doc.get("supplier_id") != supplier_id:
        return False
    if purchase_order_id and doc.get("purchase_order_id") != purchase_order_id:
        return False
    if purchase_receipt_id and doc.get("purchase_receipt_id") != purchase_receipt_id:
        return False
    if status_badge and doc.get("status_badge") != status_badge:
        return False
    if (
        transmission_status
        and doc.get("etax_summary", {}).get("transmission_status") != transmission_status
    ):
        return False
    return not (
        match_status and doc.get("matching_summary", {}).get("match_status") != match_status
    )


def _ensure_etax_invoice_ref(
    *,
    doc_id: str,
    doc: dict[str, Any],
    user: CurrentUserDep,
) -> str | None:
    """세금이 있으면 전자세금계산서 초안을 연결한다."""
    etax_ref = str(doc.get("etax_invoice_ref") or "").strip()
    if etax_ref:
        return etax_ref
    if not doc.get("taxes"):
        return None

    etax_id = generate_name(_ETAX_PREFIX, tenant_id=user.tenant_id)
    _get_etax_repo(user.tenant_id).insert(
        {
            "_id": etax_id,
            "tenant_id": user.tenant_id,
            "invoice_ref": doc_id,
            "issue_date": (
                _to_date(doc.get("posting_date")) or datetime.now(UTC).date()
            ).isoformat(),
            "supplier_or_customer": doc.get("supplier_name", ""),
            "supply_amount": float(_resolve_net_total(doc)),
            "tax_amount": float(_sum_tax_amount(doc.get("taxes", []))),
            "transmission_status": "pending",
            "docstatus": DocStatus.DRAFT,
            "created_by": user.sub,
            "updated_by": user.sub,
        }
    )
    return etax_id


def _validate_three_way_matching(doc: dict[str, Any], *, tenant_id: str) -> None:
    """참조 문서와 수량/금액이 일치하는지 확인한다."""
    matching_summary = _build_matching_summary(doc, tenant_id=tenant_id)
    if matching_summary["match_status"] in {"variance", "reference_missing"}:
        raise_bad_request("ERR-BUY-054: 3-way 매칭 불일치로 제출할 수 없습니다")


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(require_permission("purchase_invoice:create"))],
)
def 구매송장_생성(body: PurchaseInvoiceCreate, user: CurrentUserDep) -> dict[str, Any]:
    """구매송장을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    items_raw = [item.model_dump() for item in body.items]
    taxes_raw = [tax.model_dump() for tax in body.taxes]
    grand_total = calculate_line_totals_with_taxes(items_raw, taxes_raw)
    net_total = _sum_item_amount(items_raw)

    invoice = PurchaseInvoice(
        _id=doc_id,
        tenant_id=user.tenant_id,
        supplier_id=body.supplier_id,
        supplier_name=body.supplier_name,
        posting_date=body.posting_date,
        due_date=body.due_date,
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
    return {"id": doc_id, "message": "구매송장이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("purchase_invoice:read"))])
def 구매송장_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    supplier_id: str | None = None,
    purchase_order_id: str | None = None,
    purchase_receipt_id: str | None = None,
    status_badge: str | None = None,
    transmission_status: str | None = None,
    match_status: str | None = None,
) -> dict[str, Any]:
    """구매송장 목록을 운영 요약과 함께 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if supplier_id:
        query["supplier_id"] = supplier_id
    if purchase_order_id:
        query["purchase_order_id"] = purchase_order_id
    if purchase_receipt_id:
        query["purchase_receipt_id"] = purchase_receipt_id

    docs = [
        _serialize_invoice(doc, tenant_id=user.tenant_id)
        for doc in list(repo.find_many(query, sort=[("created_at", -1)]))
    ]
    filtered = [
        doc
        for doc in docs
        if _matches_filters(
            doc,
            supplier_id=supplier_id,
            purchase_order_id=purchase_order_id,
            purchase_receipt_id=purchase_receipt_id,
            status_badge=status_badge,
            transmission_status=transmission_status,
            match_status=match_status,
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("purchase_invoice:read"))])
def 구매송장_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """구매송장 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found(_NOT_FOUND)
    assert doc is not None
    return _serialize_invoice(doc, tenant_id=user.tenant_id)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("purchase_invoice:write"))])
def 구매송장_수정(
    doc_id: str,
    body: PurchaseInvoiceUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """구매송장을 수정한다. 초안 상태에서만 허용한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found(_NOT_FOUND)
    assert doc is not None
    if int(doc.get("docstatus", 0) or 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    if "items" in update_data or "taxes" in update_data:
        items_raw = update_data.get("items", [item.model_dump() for item in body.items or []])
        taxes_raw = update_data.get("taxes", [tax.model_dump() for tax in body.taxes or []])
        grand_total = calculate_line_totals_with_taxes(items_raw, taxes_raw)
        update_data["items"] = items_raw
        update_data["taxes"] = taxes_raw
        update_data["net_total"] = _sum_item_amount(items_raw)
        update_data["grand_total"] = grand_total
        update_data["outstanding_amount"] = grand_total
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "구매송장이 수정되었습니다"}


@router.post(
    "/{doc_id}/submit",
    dependencies=[Depends(require_permission("purchase_invoice:submit"))],
)
def 구매송장_제출(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """구매송장을 제출하고 전자세금계산서 및 3-way 매칭을 검증한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found(_NOT_FOUND)
    assert doc is not None
    if int(doc.get("docstatus", 0) or 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    _validate_three_way_matching(doc, tenant_id=user.tenant_id)

    etax_invoice_ref = _ensure_etax_invoice_ref(doc_id=doc_id, doc=doc, user=user)
    net_total = _resolve_net_total(doc)
    grand_total = _resolve_grand_total(doc)
    update_data: dict[str, Any] = {
        "net_total": net_total,
        "grand_total": grand_total,
        "outstanding_amount": grand_total,
    }
    if etax_invoice_ref:
        update_data["etax_invoice_ref"] = etax_invoice_ref
    repo.update_by_id(doc_id, update_data)

    repo.submit_with_event(
        doc_id,
        event_type=EventType.PURCHASE_INVOICE_SUBMITTED,
        event_data={
            "doc_id": doc_id,
            "grand_total": float(grand_total),
            "net_total": float(net_total),
            "tax_total": float(grand_total - net_total),
            "supplier": doc.get("supplier_id", ""),
            "supplier_name": doc.get("supplier_name", ""),
            "posting_date": str(doc.get("posting_date", "")),
            "due_date": str(doc.get("due_date", "")),
            "etax_invoice_ref": etax_invoice_ref,
        },
        triggered_by=user.sub,
    )
    return {"id": doc_id, "message": "구매송장이 제출되었습니다"}


@router.post(
    "/{doc_id}/cancel",
    dependencies=[Depends(require_permission("purchase_invoice:cancel"))],
)
def 구매송장_취소(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """구매송장을 취소한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found(_NOT_FOUND)
    assert doc is not None
    if int(doc.get("docstatus", 0) or 0) != DocStatus.SUBMITTED:
        raise_bad_request("제출된 문서만 취소할 수 있습니다")

    repo.cancel(doc_id)
    return {"id": doc_id, "message": "구매송장이 취소되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("purchase_invoice:delete"))],
)
def 구매송장_삭제(doc_id: str, user: CurrentUserDep) -> None:
    """구매송장을 삭제한다. 초안 상태에서만 허용한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found(_NOT_FOUND)
    assert doc is not None
    if int(doc.get("docstatus", 0) or 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 삭제할 수 있습니다")
    repo.delete_by_id(doc_id)
