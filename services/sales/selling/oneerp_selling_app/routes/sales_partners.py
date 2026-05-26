"""판매 파트너(SalesPartner) 커스텀 라우터.

고객 배정, 파트너별 매출/수금 워크벤치, 거래 이력 삭제 차단을 제공한다.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_selling_app.models.sales_partner import (
    SalesPartner,
    SalesPartnerCreate,
    SalesPartnerUpdate,
)

router = APIRouter(prefix="/api/v1/sales-partners", tags=["판매 파트너"])

_COLLECTION = "sales_partners"
_CUSTOMER_COLLECTION = "customers"
_INVOICE_COLLECTION = "sales_invoices"
_PREFIX = "SPAR"
_NOT_FOUND_MESSAGE = "판매 파트너를 찾을 수 없습니다"


def _get_partner_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_customer_repo(tenant_id: str) -> Repository:
    return Repository(_CUSTOMER_COLLECTION, tenant_id=tenant_id)


def _get_invoice_repo(tenant_id: str) -> Repository:
    return Repository(_INVOICE_COLLECTION, tenant_id=tenant_id)


def _to_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    payload = dict(document)
    if "_id" in payload:
        payload["id"] = payload["_id"]
    return payload


def _sort_partners(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        documents,
        key=lambda doc: (
            not bool(doc.get("is_active", True)),
            doc.get("territory", ""),
            doc.get("partner_name", ""),
        ),
    )


def _get_linked_customers(tenant_id: str, partner_id: str) -> list[dict[str, Any]]:
    return _get_customer_repo(tenant_id).find_many(
        query={"sales_partner_id": partner_id}, limit=1000
    )


def _iter_partner_invoices(
    *,
    tenant_id: str,
    partner_id: str,
    linked_customer_ids: set[str],
) -> tuple[list[dict[str, Any]], set[str]]:
    invoices = _get_invoice_repo(tenant_id).find_many(limit=1000)
    matched: list[dict[str, Any]] = []
    historical_customer_ids: set[str] = set()
    for invoice in invoices:
        if invoice.get("docstatus", 0) not in {DocStatus.SUBMITTED, 1, "submitted", "Submitted"}:
            continue
        invoice_partner_id = str(invoice.get("sales_partner_id") or "").strip()
        customer_id = str(invoice.get("customer_id") or "").strip()
        if invoice_partner_id == partner_id or (
            not invoice_partner_id and customer_id in linked_customer_ids
        ):
            matched.append(invoice)
            if customer_id:
                historical_customer_ids.add(customer_id)
    return matched, historical_customer_ids


def _build_partner_summary(
    *,
    tenant_id: str,
    partner: dict[str, Any],
) -> dict[str, Any]:
    linked_customers = _get_linked_customers(tenant_id, str(partner.get("_id", "")))
    linked_customer_ids = {str(customer.get("_id", "")) for customer in linked_customers}
    invoices, historical_customer_ids = _iter_partner_invoices(
        tenant_id=tenant_id,
        partner_id=str(partner.get("_id", "")),
        linked_customer_ids=linked_customer_ids,
    )
    submitted_sales_amount = sum(_to_decimal(invoice.get("grand_total", 0)) for invoice in invoices)
    outstanding_amount = sum(
        _to_decimal(invoice.get("outstanding_amount", 0)) for invoice in invoices
    )
    expected_commission_amount = sum(
        (
            _to_decimal(invoice.get("grand_total", 0))
            * _to_decimal(
                invoice.get("sales_partner_commission_rate", partner.get("commission_rate", 0)),
            )
            / Decimal(100)
        ).quantize(Decimal("0.01"))
        for invoice in invoices
    )
    posting_dates = [
        str(invoice.get("posting_date"))[:10] for invoice in invoices if invoice.get("posting_date")
    ]
    return {
        "linked_customer_count": len(linked_customers),
        "historical_customer_count": len(historical_customer_ids),
        "submitted_invoice_count": len(invoices),
        "submitted_sales_amount": float(submitted_sales_amount),
        "outstanding_amount": float(outstanding_amount),
        "expected_commission_amount": float(expected_commission_amount),
        "last_invoice_posting_date": max(posting_dates) if posting_dates else None,
    }


def _status_badge(partner: dict[str, Any], summary: dict[str, Any]) -> str:
    if not partner.get("is_active", True):
        return "inactive"
    if summary["outstanding_amount"] > 0 and summary["submitted_invoice_count"] > 0:
        return "active_collection_risk"
    if summary["submitted_invoice_count"] > 0:
        return "active_revenue"
    if summary["linked_customer_count"] > 0:
        return "active_pipeline"
    return "unassigned"


def _recommended_action(status_badge: str) -> str:
    if status_badge == "inactive":
        return "reactivate_partner"
    if status_badge == "active_collection_risk":
        return "review_receivables"
    if status_badge == "active_revenue":
        return "review_commissions"
    return "assign_customer"


def _available_actions(
    *,
    status_badge: str,
    summary: dict[str, Any],
) -> list[str]:
    actions = ["assign_customer"]
    if summary["submitted_invoice_count"] > 0:
        actions.append("view_sales_history")
    if status_badge == "active_collection_risk":
        actions.append("review_receivables")
    if status_badge == "inactive":
        actions.append("reactivate_partner")
    actions.append("edit")
    return actions


def _serialize_partner(*, tenant_id: str, partner: dict[str, Any]) -> dict[str, Any]:
    payload = _with_public_id(partner)
    summary = _build_partner_summary(tenant_id=tenant_id, partner=partner)
    badge = _status_badge(partner, summary)
    payload["summary"] = summary
    payload["status_badge"] = badge
    payload["recommended_action"] = _recommended_action(badge)
    payload["available_actions"] = _available_actions(status_badge=badge, summary=summary)
    return payload


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("sales_partner:create"))]
)
def create_sales_partner(body: SalesPartnerCreate, user: CurrentUserDep) -> dict[str, Any]:
    """판매 파트너를 생성한다."""
    repo = _get_partner_repo(user.tenant_id)
    payload = body.model_dump()
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    partner = SalesPartner(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **payload,
    )
    repo.insert(partner)
    return {"_id": doc_id, "id": doc_id, **payload}


@router.get("", dependencies=[Depends(require_permission("sales_partner:read"))])
def list_sales_partners(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    *,
    territory: str | None = None,
    partner_type: str | None = None,
    is_active: bool | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """판매 파트너 목록을 워크벤치 요약과 함께 조회한다."""
    repo = _get_partner_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if territory:
        query["territory"] = territory
    if partner_type:
        query["partner_type"] = partner_type
    if is_active is not None:
        query["is_active"] = is_active
    documents = [
        _serialize_partner(tenant_id=user.tenant_id, partner=document)
        for document in _sort_partners(repo.find_many(query=query, limit=1000))
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


@router.get("/{doc_id}", dependencies=[Depends(require_permission("sales_partner:read"))])
def get_sales_partner(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """판매 파트너 상세 정보를 조회한다."""
    repo = _get_partner_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    document = cast("dict[str, Any]", document)
    return _serialize_partner(tenant_id=user.tenant_id, partner=document)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("sales_partner:write"))])
def update_sales_partner(
    doc_id: str,
    body: SalesPartnerUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """판매 파트너를 수정한다."""
    repo = _get_partner_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    document = cast("dict[str, Any]", document)
    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return _serialize_partner(tenant_id=user.tenant_id, partner={**document, **update_data})


@router.post(
    "/{doc_id}/customers/{customer_id}",
    dependencies=[Depends(require_permission("sales_partner:write"))],
)
def assign_customer_to_sales_partner(
    doc_id: str,
    customer_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """고객을 판매 파트너에 배정한다."""
    partner = _get_partner_repo(user.tenant_id).find_by_id(doc_id)
    if not partner:
        raise_not_found(_NOT_FOUND_MESSAGE)
    partner = cast("dict[str, Any]", partner)
    if not partner.get("is_active", True):
        raise_unprocessable("ERR-SELL-041", "비활성 판매 파트너에는 고객을 배정할 수 없습니다")

    customer_repo = _get_customer_repo(user.tenant_id)
    customer = customer_repo.find_by_id(customer_id)
    if not customer:
        raise_not_found("고객을 찾을 수 없습니다")
    customer = cast("dict[str, Any]", customer)

    customer_repo.update_by_id(
        customer_id,
        {
            "sales_partner_id": doc_id,
            "sales_partner_name": partner.get("partner_name", ""),
        },
    )
    return {
        "partner_id": doc_id,
        "customer_id": customer_id,
        "partner_name": partner.get("partner_name", ""),
        "message": "고객이 판매 파트너에 배정되었습니다",
    }


@router.delete(
    "/{doc_id}/customers/{customer_id}",
    dependencies=[Depends(require_permission("sales_partner:write"))],
)
def unassign_customer_from_sales_partner(
    doc_id: str,
    customer_id: str,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """고객의 판매 파트너 연결을 해제한다."""
    partner = _get_partner_repo(user.tenant_id).find_by_id(doc_id)
    if not partner:
        raise_not_found(_NOT_FOUND_MESSAGE)
    partner = cast("dict[str, Any]", partner)

    customer_repo = _get_customer_repo(user.tenant_id)
    customer = customer_repo.find_by_id(customer_id)
    if not customer:
        raise_not_found("고객을 찾을 수 없습니다")
    customer = cast("dict[str, Any]", customer)
    if customer.get("sales_partner_id") != doc_id:
        raise_unprocessable("ERR-SELL-043", "해당 고객은 이 판매 파트너에 연결되어 있지 않습니다")

    customer_repo.update_by_id(
        customer_id,
        {
            "sales_partner_id": None,
            "sales_partner_name": None,
        },
    )
    return {
        "partner_id": doc_id,
        "customer_id": customer_id,
        "message": "고객의 판매 파트너 연결이 해제되었습니다",
    }


@router.get("/{doc_id}/summary", dependencies=[Depends(require_permission("sales_partner:read"))])
def get_sales_partner_summary(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """판매 파트너별 고객/매출/미수/예상 수수료 요약을 반환한다."""
    partner = _get_partner_repo(user.tenant_id).find_by_id(doc_id)
    if not partner:
        raise_not_found(_NOT_FOUND_MESSAGE)
    partner = cast("dict[str, Any]", partner)
    serialized = _serialize_partner(tenant_id=user.tenant_id, partner=partner)
    return {
        "partner": _with_public_id(partner),
        "summary": serialized["summary"],
        "status_badge": serialized["status_badge"],
        "recommended_action": serialized["recommended_action"],
        "available_actions": serialized["available_actions"],
    }


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("sales_partner:delete"))],
)
def delete_sales_partner(doc_id: str, user: CurrentUserDep) -> None:
    """현재 연결 고객 또는 제출된 매출 이력이 있는 판매 파트너는 삭제할 수 없다."""
    repo = _get_partner_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    document = cast("dict[str, Any]", document)
    linked_customers = _get_linked_customers(user.tenant_id, doc_id)
    if linked_customers:
        raise_unprocessable("ERR-SELL-042", "고객이 연결된 판매 파트너는 삭제할 수 없습니다")
    summary = _build_partner_summary(tenant_id=user.tenant_id, partner=document)
    if summary["submitted_invoice_count"] > 0:
        raise_unprocessable("ERR-SELL-044", "거래 이력이 있는 판매 파트너는 삭제할 수 없습니다")
    repo.delete_by_id(doc_id)
