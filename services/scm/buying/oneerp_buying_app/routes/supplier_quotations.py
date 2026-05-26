"""공급업체견적(Supplier Quotation) 워크벤치 라우터."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found, raise_unprocessable
from oneerp_core.events.schemas import EventType
from oneerp_core.line_items import calculate_line_totals
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_buying_app.models.supplier_quotation import (
    SupplierQuotation,
    SupplierQuotationCreate,
    SupplierQuotationUpdate,
)
from oneerp_buying_app.services.purchase_process_service import PurchaseProcessService

router = APIRouter(prefix="/api/v1/supplier-quotations", tags=["공급업체견적"])

_COLLECTION = "supplier_quotations"
_RFQ_COLLECTION = "request_for_quotations"
_PURCHASE_ORDER_COLLECTION = "purchase_orders"
_PREFIX = "SQ"
_NOT_FOUND = "공급업체견적을 찾을 수 없습니다"


def _get_repo(tenant_id: str) -> Repository:
    """공급업체견적 저장소를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_rfq_repo(tenant_id: str) -> Repository:
    """견적요청 저장소를 생성한다."""
    return Repository(_RFQ_COLLECTION, tenant_id=tenant_id)


def _get_purchase_order_repo(tenant_id: str) -> Repository:
    """구매주문 저장소를 생성한다."""
    return Repository(_PURCHASE_ORDER_COLLECTION, tenant_id=tenant_id)


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    payload = dict(document)
    if "_id" in payload:
        payload["id"] = payload["_id"]
    return payload


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


def _sum_qty(items: list[dict[str, Any]]) -> Decimal:
    return sum((_to_decimal(item.get("qty", 0)) for item in items), Decimal(0))


def _submitted_quotations(tenant_id: str, rfq_reference: str) -> list[dict[str, Any]]:
    if not rfq_reference:
        return []
    return list(
        _get_repo(tenant_id).find_many(
            query={"rfq_reference": rfq_reference, "docstatus": DocStatus.SUBMITTED},
            limit=1000,
            sort=[("grand_total", 1), ("created_at", 1)],
        )
    )


def _linked_purchase_orders(tenant_id: str, quotation_id: str) -> list[dict[str, Any]]:
    return list(
        _get_purchase_order_repo(tenant_id).find_many(
            query={"quotation_reference": quotation_id},
            limit=1000,
            sort=[("created_at", -1)],
        )
    )


def _build_summary(tenant_id: str, quotation: dict[str, Any]) -> dict[str, Any]:
    rfq_reference = str(quotation.get("rfq_reference", "") or "")
    rfq_doc = _get_rfq_repo(tenant_id).find_by_id(rfq_reference) if rfq_reference else None
    submitted_quotes = _submitted_quotations(tenant_id, rfq_reference)
    linked_purchase_orders = _linked_purchase_orders(tenant_id, str(quotation.get("_id", "")))

    comparison_rank: int | None = None
    if quotation.get("docstatus", 0) == DocStatus.SUBMITTED:
        for index, document in enumerate(submitted_quotes, start=1):
            if document.get("_id") == quotation.get("_id"):
                comparison_rank = index
                break

    return {
        "item_count": len(quotation.get("items", [])),
        "total_qty": float(_sum_qty(quotation.get("items", []))),
        "submitted_quote_count": len(submitted_quotes),
        "rfq_supplier_count": len(rfq_doc.get("suppliers", [])) if rfq_doc else 0,
        "comparison_rank": comparison_rank,
        "linked_purchase_order_count": len(linked_purchase_orders),
        "is_lowest_quote": comparison_rank == 1 if comparison_rank is not None else False,
    }


def _status_badge(quotation: dict[str, Any], summary: dict[str, Any]) -> str:
    docstatus = int(quotation.get("docstatus", 0) or 0)
    if docstatus == DocStatus.DRAFT:
        return "draft"
    if docstatus == DocStatus.CANCELLED:
        return "cancelled"
    if summary["linked_purchase_order_count"] > 0:
        return "selected_for_order"
    if summary["is_lowest_quote"]:
        return "best_offer"
    if summary["submitted_quote_count"] > 1:
        return "competing_quote"
    return "submitted"


def _recommended_action(status_badge: str) -> str:
    if status_badge == "draft":
        return "submit"
    if status_badge == "cancelled":
        return "duplicate_quote"
    if status_badge == "selected_for_order":
        return "review_purchase_order"
    if status_badge == "best_offer":
        return "create_purchase_order"
    return "compare_quotations"


def _available_actions(
    *,
    quotation: dict[str, Any],
    summary: dict[str, Any],
    status_badge: str,
) -> list[str]:
    actions: list[str]
    rfq_reference = str(quotation.get("rfq_reference", "") or "")
    if status_badge == "draft":
        actions = ["edit", "submit", "delete"]
        if rfq_reference:
            actions.append("view_rfq")
    elif status_badge == "cancelled":
        actions = []
        if rfq_reference:
            actions.append("view_rfq")
    else:
        actions = ["compare_quotations"]
        if summary["linked_purchase_order_count"] > 0:
            actions.append("open_purchase_order")
        elif status_badge == "best_offer":
            actions.append("create_purchase_order")
        if rfq_reference:
            actions.append("view_rfq")
        actions.append("cancel")
    return actions


def _serialize_quotation(tenant_id: str, quotation: dict[str, Any]) -> dict[str, Any]:
    payload = _with_public_id(quotation)
    summary = _build_summary(tenant_id, payload)
    status_badge = _status_badge(payload, summary)
    payload["summary"] = summary
    payload["status_badge"] = status_badge
    payload["recommended_action"] = _recommended_action(status_badge)
    payload["available_actions"] = _available_actions(
        quotation=payload,
        summary=summary,
        status_badge=status_badge,
    )
    return payload


def _build_workbench_summary(documents: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "draft_count": sum(1 for document in documents if document.get("status_badge") == "draft"),
        "submitted_count": sum(
            1
            for document in documents
            if document.get("status_badge")
            in {"best_offer", "competing_quote", "submitted", "selected_for_order"}
        ),
        "cancelled_count": sum(
            1 for document in documents if document.get("status_badge") == "cancelled"
        ),
        "best_offer_count": sum(
            1 for document in documents if document.get("status_badge") == "best_offer"
        ),
        "selected_for_order_count": sum(
            1 for document in documents if document.get("status_badge") == "selected_for_order"
        ),
        "total_quoted_amount": float(
            sum(
                (_to_decimal(document.get("grand_total", 0)) for document in documents),
                Decimal(0),
            )
        ),
    }


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("supplier_quotation:create"))]
)
def 공급업체견적_생성(body: SupplierQuotationCreate, user: CurrentUserDep) -> dict[str, Any]:
    """공급업체견적을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    items_raw = [item.model_dump() for item in body.items]
    items_raw, total = calculate_line_totals(items_raw)

    quotation = SupplierQuotation(
        _id=doc_id,
        tenant_id=user.tenant_id,
        rfq_reference=body.rfq_reference,
        supplier=body.supplier,
        supplier_name=body.supplier_name,
        transaction_date=body.transaction_date,
        valid_till=body.valid_till,
        items=body.items,
        total=total,
        grand_total=total,
        created_by=user.sub,
        updated_by=user.sub,
    )
    doc_dict = quotation.model_dump(by_alias=True, exclude_none=True)
    doc_dict["items"] = items_raw
    repo.insert(doc_dict)

    return {"id": doc_id, "message": "공급업체견적이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("supplier_quotation:read"))])
def 공급업체견적_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    rfq_reference: str | None = None,
    supplier: str | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """공급업체견적 목록과 비교 워크벤치 요약을 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if rfq_reference:
        query["rfq_reference"] = rfq_reference
    if supplier:
        query["supplier"] = supplier

    documents = [
        _serialize_quotation(user.tenant_id, document)
        for document in repo.find_many(query=query, limit=1000, sort=[("created_at", -1)])
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
        "summary": _build_workbench_summary(documents),
    }


@router.get(
    "/compare/{rfq_id}",
    dependencies=[Depends(require_permission("supplier_quotation:read"))],
)
def 공급업체견적_비교(rfq_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """RFQ별 제출된 공급업체견적 비교표와 추천 공급업체를 반환한다."""
    service = PurchaseProcessService(user.tenant_id)
    return service.compare_quotations(rfq_id)


@router.get("/{doc_id}", dependencies=[Depends(require_permission("supplier_quotation:read"))])
def 공급업체견적_조회(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """공급업체견적 상세와 비교 워크벤치 요약을 조회한다."""
    doc = _get_repo(user.tenant_id).find_by_id(doc_id)
    if doc is None:
        raise_not_found(_NOT_FOUND)
    assert doc is not None
    return _serialize_quotation(user.tenant_id, doc)


@router.get(
    "/{doc_id}/summary",
    dependencies=[Depends(require_permission("supplier_quotation:read"))],
)
def 공급업체견적_요약(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """RFQ 카드/요약 패널에 필요한 공급업체견적 요약을 반환한다."""
    doc = _get_repo(user.tenant_id).find_by_id(doc_id)
    if doc is None:
        raise_not_found(_NOT_FOUND)
    assert doc is not None
    payload = _serialize_quotation(user.tenant_id, doc)
    return {
        "supplier_quotation": _with_public_id(doc),
        "summary": payload["summary"],
        "status_badge": payload["status_badge"],
        "recommended_action": payload["recommended_action"],
        "available_actions": payload["available_actions"],
    }


@router.put("/{doc_id}", dependencies=[Depends(require_permission("supplier_quotation:write"))])
def 공급업체견적_수정(
    doc_id: str,
    body: SupplierQuotationUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """공급업체견적을 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found(_NOT_FOUND)
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    if "items" in update_data:
        items_raw = update_data["items"]
        items_raw, total = calculate_line_totals(items_raw)
        update_data["items"] = items_raw
        update_data["total"] = total
        update_data["grand_total"] = total
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return _serialize_quotation(user.tenant_id, {**doc, **update_data})


@router.post(
    "/{doc_id}/submit", dependencies=[Depends(require_permission("supplier_quotation:submit"))]
)
def 공급업체견적_제출(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """공급업체견적을 제출한다 (초안 -> 제출)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found(_NOT_FOUND)
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 제출할 수 있습니다")

    repo.submit_with_event(
        doc_id, event_type=EventType.SUPPLIER_QUOTATION_SUBMITTED, triggered_by=user.sub
    )
    return {"id": doc_id, "message": "공급업체견적이 제출되었습니다"}


@router.post(
    "/{doc_id}/cancel", dependencies=[Depends(require_permission("supplier_quotation:cancel"))]
)
def 공급업체견적_취소(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """공급업체견적을 취소한다 (제출 -> 취소)."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found(_NOT_FOUND)
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.SUBMITTED:
        raise_bad_request("제출된 문서만 취소할 수 있습니다")

    repo.cancel(doc_id)
    return {"id": doc_id, "message": "공급업체견적이 취소되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("supplier_quotation:delete"))],
)
def 공급업체견적_삭제(doc_id: str, user: CurrentUserDep) -> None:
    """공급업체견적을 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise_not_found(_NOT_FOUND)
    assert doc is not None
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_unprocessable("ERR-BUY-030", "제출/취소된 문서는 수정할 수 없습니다")
    if _linked_purchase_orders(user.tenant_id, doc_id):
        raise_unprocessable("ERR-BUY-047", "발주로 전환된 견적은 삭제할 수 없습니다")

    repo.delete_by_id(doc_id)
