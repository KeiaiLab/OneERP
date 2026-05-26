"""공급업체(Supplier) 워크벤치 라우트."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_buying_app.models.supplier import Supplier, SupplierCreate, SupplierUpdate

router = APIRouter(prefix="/api/v1/suppliers", tags=["공급업체"])

_COLLECTION = "suppliers"
_PURCHASE_ORDER_COLLECTION = "purchase_orders"
_PURCHASE_RECEIPT_COLLECTION = "purchase_receipts"
_PURCHASE_INVOICE_COLLECTION = "purchase_invoices"
_SCORECARD_COLLECTION = "supplier_scorecards"
_PREFIX = "SUP"
_NOT_FOUND_MESSAGE = "공급업체를 찾을 수 없습니다"


def _get_repo(tenant_id: str, collection: str = _COLLECTION) -> Repository:
    return Repository(collection, tenant_id=tenant_id)


def _get_purchase_order_repo(tenant_id: str) -> Repository:
    return _get_repo(tenant_id, _PURCHASE_ORDER_COLLECTION)


def _get_purchase_receipt_repo(tenant_id: str) -> Repository:
    return _get_repo(tenant_id, _PURCHASE_RECEIPT_COLLECTION)


def _get_purchase_invoice_repo(tenant_id: str) -> Repository:
    return _get_repo(tenant_id, _PURCHASE_INVOICE_COLLECTION)


def _get_scorecard_repo(tenant_id: str) -> Repository:
    return _get_repo(tenant_id, _SCORECARD_COLLECTION)


def _normalize_supplied_items(items: list[str]) -> list[str]:
    normalized: list[str] = []
    for item in items:
        value = str(item).strip()
        if value and value not in normalized:
            normalized.append(value)
    return normalized


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    payload = dict(document)
    if "_id" in payload:
        payload["id"] = payload["_id"]
    if "supplied_items" in payload:
        payload["supplied_items"] = _normalize_supplied_items(
            list(payload.get("supplied_items", []))
        )
    return payload


def _to_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _sort_suppliers(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        documents,
        key=lambda doc: (
            not bool(doc.get("is_active", True)),
            str(doc.get("supplier_group", "") or ""),
            str(doc.get("supplier_name", "") or ""),
        ),
    )


def _latest_scorecard(scorecards: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not scorecards:
        return None
    latest = max(
        scorecards,
        key=lambda document: (
            str(document.get("evaluation_period", "")),
            str(document.get("_id", "")),
        ),
    )
    return _with_public_id(latest)


def _build_supplier_summary(tenant_id: str, supplier_id: str) -> dict[str, Any]:
    purchase_orders = [
        document
        for document in _get_purchase_order_repo(tenant_id).find_many(
            query={"supplier_id": supplier_id},
            limit=1000,
        )
        if document.get("docstatus", 0) == 1
    ]
    purchase_receipts = [
        document
        for document in _get_purchase_receipt_repo(tenant_id).find_many(
            query={"supplier": supplier_id},
            limit=1000,
        )
        if document.get("docstatus", 0) == 1
    ]
    purchase_invoices = [
        document
        for document in _get_purchase_invoice_repo(tenant_id).find_many(
            query={"supplier_id": supplier_id},
            limit=1000,
        )
        if document.get("docstatus", 0) == 1
    ]
    scorecards = _get_scorecard_repo(tenant_id).find_many(
        query={"supplier": supplier_id}, limit=1000
    )

    submitted_order_amount = sum(
        _to_decimal(document.get("total", 0)) for document in purchase_orders
    )
    submitted_invoice_amount = sum(
        _to_decimal(document.get("grand_total", 0)) for document in purchase_invoices
    )
    outstanding_amount = sum(
        _to_decimal(document.get("outstanding_amount", 0)) for document in purchase_invoices
    )

    return {
        "submitted_purchase_order_count": len(purchase_orders),
        "submitted_purchase_receipt_count": len(purchase_receipts),
        "submitted_purchase_invoice_count": len(purchase_invoices),
        "submitted_order_amount": float(submitted_order_amount),
        "submitted_invoice_amount": float(submitted_invoice_amount),
        "outstanding_amount": float(outstanding_amount),
        "scorecard_count": len(scorecards),
        "latest_scorecard": _latest_scorecard(scorecards),
    }


def _status_badge(supplier: dict[str, Any], summary: dict[str, Any]) -> str:
    if not supplier.get("is_active", True):
        return "inactive"
    if summary["outstanding_amount"] > 0:
        return "payment_due"
    latest_scorecard = summary.get("latest_scorecard")
    if latest_scorecard and _to_decimal(latest_scorecard.get("total_score", 0)) < Decimal(80):
        return "performance_watch"
    if (
        summary["submitted_purchase_order_count"] > 0
        or summary["submitted_purchase_receipt_count"] > 0
        or summary["submitted_purchase_invoice_count"] > 0
    ):
        return "active_supplier"
    return "onboarding"


def _recommended_action(status_badge: str) -> str:
    if status_badge == "inactive":
        return "reactivate_supplier"
    if status_badge == "payment_due":
        return "review_payables"
    if status_badge == "performance_watch":
        return "review_scorecard"
    if status_badge == "active_supplier":
        return "create_purchase_order"
    return "update_supplier_profile"


def _available_actions(
    *,
    supplier: dict[str, Any],
    summary: dict[str, Any],
) -> list[str]:
    actions = ["edit"]
    if supplier.get("is_active", True):
        actions.append("create_purchase_order")
    else:
        actions.append("reactivate_supplier")
    if (
        summary["submitted_purchase_order_count"] > 0
        or summary["submitted_purchase_receipt_count"] > 0
        or summary["submitted_purchase_invoice_count"] > 0
    ):
        actions.append("open_purchase_history")
    if summary["outstanding_amount"] > 0:
        actions.append("open_accounts_payable")
    if summary["scorecard_count"] > 0:
        actions.append("view_scorecards")
    return actions


def _serialize_supplier(*, tenant_id: str, supplier: dict[str, Any]) -> dict[str, Any]:
    payload = _with_public_id(supplier)
    summary = _build_supplier_summary(tenant_id, str(supplier.get("_id", "")))
    status_badge = _status_badge(supplier, summary)
    payload["summary"] = summary
    payload["status_badge"] = status_badge
    payload["recommended_action"] = _recommended_action(status_badge)
    payload["available_actions"] = _available_actions(supplier=supplier, summary=summary)
    return payload


def _has_linked_transactions(tenant_id: str, supplier_id: str) -> bool:
    return any(
        (
            _get_purchase_order_repo(tenant_id).count(query={"supplier_id": supplier_id}) > 0,
            _get_purchase_receipt_repo(tenant_id).count(query={"supplier": supplier_id}) > 0,
            _get_purchase_invoice_repo(tenant_id).count(query={"supplier_id": supplier_id}) > 0,
            _get_scorecard_repo(tenant_id).count(query={"supplier": supplier_id}) > 0,
        ),
    )


@router.post("", status_code=201, dependencies=[Depends(require_permission("supplier:create"))])
def create_supplier(body: SupplierCreate, user: CurrentUserDep) -> dict[str, Any]:
    """공급업체를 생성한다."""
    repo = _get_repo(user.tenant_id)
    payload = body.model_dump(exclude_none=True)
    payload["supplied_items"] = _normalize_supplied_items(list(payload.get("supplied_items", [])))
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    supplier = Supplier(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **payload,
    )
    repo.insert(supplier)
    return _with_public_id({"_id": doc_id, **payload})


@router.get("", dependencies=[Depends(require_permission("supplier:read"))])
def list_suppliers(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    supplier_group: str | None = None,
    supplier_type: str | None = None,
    country: str | None = None,
    *,
    is_active: bool | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """공급업체 목록과 워크벤치 요약을 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if supplier_group:
        query["supplier_group"] = supplier_group
    if supplier_type:
        query["supplier_type"] = supplier_type
    if country:
        query["country"] = country
    if is_active is not None:
        query["is_active"] = is_active

    documents = [
        _serialize_supplier(tenant_id=user.tenant_id, supplier=document)
        for document in _sort_suppliers(repo.find_many(query=query, limit=1000))
    ]
    if status_badge:
        documents = [
            document for document in documents if document.get("status_badge") == status_badge
        ]

    total = len(documents)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": documents[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("supplier:read"))])
def get_supplier(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """공급업체 상세와 워크벤치 요약을 조회한다."""
    document = _get_repo(user.tenant_id).find_by_id(doc_id)
    if document is None:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    return _serialize_supplier(tenant_id=user.tenant_id, supplier=document)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("supplier:write"))])
def update_supplier(doc_id: str, body: SupplierUpdate, user: CurrentUserDep) -> dict[str, Any]:
    """공급업체를 수정한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if document is None:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    update_data = body.model_dump(exclude_none=True)
    if "supplied_items" in update_data:
        update_data["supplied_items"] = _normalize_supplied_items(
            list(update_data["supplied_items"])
        )
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return _serialize_supplier(tenant_id=user.tenant_id, supplier={**document, **update_data})


@router.get("/{doc_id}/summary", dependencies=[Depends(require_permission("supplier:read"))])
def get_supplier_summary(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """공급업체 거래 요약 카드 데이터를 반환한다."""
    supplier = _get_repo(user.tenant_id).find_by_id(doc_id)
    if supplier is None:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert supplier is not None
    summary = _build_supplier_summary(user.tenant_id, doc_id)
    status_badge = _status_badge(supplier, summary)
    return {
        "supplier": _with_public_id(supplier),
        "summary": summary,
        "status_badge": status_badge,
        "recommended_action": _recommended_action(status_badge),
        "available_actions": _available_actions(supplier=supplier, summary=summary),
    }


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("supplier:delete"))],
)
def delete_supplier(doc_id: str, user: CurrentUserDep) -> None:
    """거래 이력이 있는 공급업체는 삭제할 수 없다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if document is None:
        raise_not_found(_NOT_FOUND_MESSAGE)
    assert document is not None
    if _has_linked_transactions(user.tenant_id, doc_id):
        raise_unprocessable("ERR-BUY-046", "거래 이력이 있는 공급업체는 삭제할 수 없습니다")
    repo.delete_by_id(doc_id)
