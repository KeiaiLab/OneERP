"""부가세 신고(VAT Return) 워크벤치 라우터."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from oneerp_core.route_helpers import check_draft_status, delete_draft, get_or_404

from ..models.vat_return import VATReturn, VATReturnCreate, VATReturnUpdate
from ..services.vat_service import VATService

router = APIRouter(prefix="/api/v1/vat-returns", tags=["부가세 신고"])

_COLLECTION = "vat_returns"
_PREFIX = "VAT"
_NOT_FOUND = "부가세 신고를 찾을 수 없습니다"
_PAGE_LIMIT = 500
_today_fn = date.today


def _today() -> date:
    return _today_fn()


def _get_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_etax_invoice_repo(tenant_id: str) -> Repository:
    return Repository("etax_invoices", tenant_id=tenant_id)


def _get_vat_service(tenant_id: str) -> VATService:
    return VATService(tenant_id=tenant_id)


def _to_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _to_float(value: Decimal) -> float:
    return float(value)


def _quarter_to_range(period: str) -> tuple[date, date]:
    try:
        year_text, quarter_text = period.split("-Q", maxsplit=1)
        year = int(year_text)
        quarter = int(quarter_text)
    except ValueError:
        raise_unprocessable("ERR-KTAX-021", "신고 기간은 YYYY-QN 형식이어야 합니다")

    quarter_ranges = {
        1: (date(year, 1, 1), date(year, 3, 31)),
        2: (date(year, 4, 1), date(year, 6, 30)),
        3: (date(year, 7, 1), date(year, 9, 30)),
        4: (date(year, 10, 1), date(year, 12, 31)),
    }
    try:
        return quarter_ranges[quarter]
    except KeyError:
        raise_unprocessable("ERR-KTAX-021", "신고 분기는 1~4분기만 지원합니다")


def _parse_period_range(period: str) -> tuple[date, date]:
    period_text = str(period or "").strip()
    if not period_text:
        raise_unprocessable("ERR-KTAX-021", "신고 기간은 필수입니다")
    if "~" in period_text:
        start_text, end_text = period_text.split("~", maxsplit=1)
        return (date.fromisoformat(start_text), date.fromisoformat(end_text))
    return _quarter_to_range(period_text)


def _compute_due_date(period: str, period_end: date) -> date:
    period_text = str(period or "").strip()
    if "-Q4" in period_text:
        return date(period_end.year + 1, 1, 25)
    if "-Q1" in period_text:
        return date(period_end.year, 4, 25)
    if "-Q2" in period_text:
        return date(period_end.year, 7, 25)
    if "-Q3" in period_text:
        return date(period_end.year, 10, 25)
    if period_end.month <= 3:
        return date(period_end.year, 4, 25)
    if period_end.month <= 6:
        return date(period_end.year, 7, 25)
    if period_end.month <= 9:
        return date(period_end.year, 10, 25)
    return date(period_end.year + 1, 1, 25)


def _build_invoice_sync_summary(
    etax_repo: Repository,
    *,
    period_start: date,
    period_end: date,
) -> dict[str, int]:
    docs = etax_repo.find_many(
        {"issue_date": {"$gte": period_start, "$lte": period_end}},
        limit=_PAGE_LIMIT,
    )
    issued_count = len(docs)
    transmitted_count = sum(1 for doc in docs if doc.get("transmission_status") == "transmitted")
    pending_count = sum(1 for doc in docs if doc.get("transmission_status") == "pending")
    failed_count = sum(1 for doc in docs if doc.get("transmission_status") == "failed")
    return {
        "issued_count": issued_count,
        "transmitted_count": transmitted_count,
        "pending_count": pending_count,
        "failed_count": failed_count,
    }


def _build_tax_summary(doc: dict[str, Any]) -> dict[str, float]:
    net_tax = _to_decimal(doc.get("net_tax"))
    payable_tax = net_tax if net_tax > 0 else Decimal(0)
    refundable_tax = abs(net_tax) if net_tax < 0 else Decimal(0)
    return {
        "output_tax": _to_float(_to_decimal(doc.get("output_tax"))),
        "input_tax": _to_float(_to_decimal(doc.get("input_tax"))),
        "net_tax": _to_float(net_tax),
        "payable_tax": _to_float(payable_tax),
        "refundable_tax": _to_float(refundable_tax),
    }


def _build_period_scope_summary(
    *,
    period: str,
    period_start: date,
    period_end: date,
) -> dict[str, str]:
    return {
        "period": period,
        "period_start": period_start.isoformat(),
        "period_end": period_end.isoformat(),
        "filing_cycle": "quarterly",
        "due_date": _compute_due_date(period, period_end).isoformat(),
    }


def _resolve_status_badge(
    doc: dict[str, Any],
    *,
    due_date: date,
) -> str:
    status = str(doc.get("status") or "draft")
    net_tax = _to_decimal(doc.get("net_tax"))

    if status == "cancelled" or int(doc.get("docstatus", DocStatus.DRAFT)) == DocStatus.CANCELLED:
        return "cancelled"
    if status == "submitted" or int(doc.get("docstatus", DocStatus.DRAFT)) == DocStatus.SUBMITTED:
        return "submitted_refund" if net_tax < 0 else "submitted_payable"
    if due_date < _today():
        return "overdue_draft"
    return "draft_refund" if net_tax < 0 else "draft_payable"


def _resolve_recommended_action(status_badge: str) -> str:
    if status_badge in {"draft_payable", "overdue_draft"}:
        return "submit_vat_return"
    if status_badge == "draft_refund":
        return "review_refund_documents"
    if status_badge == "submitted_payable":
        return "schedule_tax_payment"
    if status_badge == "submitted_refund":
        return "track_tax_refund"
    return "regenerate_filing"


def _build_available_actions(doc: dict[str, Any], status_badge: str) -> list[str]:
    actions: list[str] = ["open_etax_invoices"]
    docstatus = int(doc.get("docstatus", DocStatus.DRAFT))

    if docstatus == DocStatus.DRAFT:
        actions = ["edit", "preview_filing", "submit", *actions]
    elif docstatus == DocStatus.SUBMITTED:
        actions = ["view_filing_history", *actions]
        if status_badge == "submitted_payable":
            actions.append("schedule_tax_payment")
        else:
            actions.append("track_tax_refund")
        actions.append("cancel")
    else:
        actions = ["view_filing_history", *actions, "regenerate_filing"]
    return actions


def _serialize_vat_return(
    doc: dict[str, Any],
    *,
    etax_repo: Repository,
) -> dict[str, Any]:
    payload = dict(doc)
    period = str(doc.get("period") or "")
    period_start, period_end = _parse_period_range(period)
    period_scope_summary = _build_period_scope_summary(
        period=period,
        period_start=period_start,
        period_end=period_end,
    )
    invoice_sync_summary = _build_invoice_sync_summary(
        etax_repo,
        period_start=period_start,
        period_end=period_end,
    )
    status_badge = _resolve_status_badge(
        doc,
        due_date=date.fromisoformat(period_scope_summary["due_date"]),
    )

    payload["id"] = str(doc.get("_id") or "")
    payload["tax_summary"] = _build_tax_summary(doc)
    payload["period_scope_summary"] = period_scope_summary
    payload["invoice_sync_summary"] = invoice_sync_summary
    payload["status_badge"] = status_badge
    payload["recommended_action"] = _resolve_recommended_action(status_badge)
    payload["available_actions"] = _build_available_actions(doc, status_badge)
    return payload


def _matches_filters(doc: dict[str, Any], *, status_badge: str | None) -> bool:
    return not (status_badge and doc.get("status_badge") != status_badge)


def _build_listing_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "draft_count": sum(1 for row in rows if row.get("status") == "draft"),
        "submitted_count": sum(1 for row in rows if row.get("status") == "submitted"),
        "cancelled_count": sum(1 for row in rows if row.get("status") == "cancelled"),
        "payable_count": sum(1 for row in rows if row["tax_summary"]["payable_tax"] > 0),
        "refund_count": sum(1 for row in rows if row["tax_summary"]["refundable_tax"] > 0),
        "overdue_count": sum(1 for row in rows if row.get("status_badge") == "overdue_draft"),
    }


@router.post("", status_code=201, dependencies=[Depends(require_permission("vat_return:create"))])
def create_vat_return(body: VATReturnCreate, user: CurrentUserDep) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    etax_repo = _get_etax_invoice_repo(user.tenant_id)

    existing = repo.find_many(
        {"period": body.period, "docstatus": {"$ne": DocStatus.CANCELLED}},
        limit=1,
    )
    if existing:
        raise_unprocessable(
            "ERR-KTAX-020",
            f"해당 기간의 부가세 신고서가 이미 존재합니다: {body.period}",
        )

    output_tax = _to_decimal(body.output_tax)
    input_tax = _to_decimal(body.input_tax)
    net_tax = _to_decimal(body.net_tax)
    tax_amount = _to_decimal(body.tax_amount)

    if all(value == 0 for value in (output_tax, input_tax, net_tax, tax_amount)):
        period_start, period_end = _parse_period_range(body.period)
        result = _get_vat_service(user.tenant_id).calculate_vat(period_start, period_end)
        output_tax = _to_decimal(result["output_tax"])
        input_tax = _to_decimal(result["input_tax"])
        net_tax = _to_decimal(result["net_tax"])
        tax_amount = net_tax
    elif net_tax == 0 and (output_tax != 0 or input_tax != 0):
        net_tax = output_tax - input_tax
        tax_amount = net_tax

    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    vat_return = VATReturn(
        _id=doc_id,
        tenant_id=user.tenant_id,
        period=body.period,
        tax_amount=tax_amount,
        filing_date=body.filing_date,
        status="draft",
        output_tax=output_tax,
        input_tax=input_tax,
        net_tax=net_tax,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(vat_return)
    created = get_or_404(repo, doc_id, _NOT_FOUND)
    return _serialize_vat_return(created, etax_repo=etax_repo)


@router.get("", dependencies=[Depends(require_permission("vat_return:read"))])
def list_vat_returns(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    status_badge: str | None = None,
) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    etax_repo = _get_etax_invoice_repo(user.tenant_id)
    docs = repo.find_many({}, limit=_PAGE_LIMIT, sort=[("period", -1), ("created_at", -1)])
    rows = [
        serialized
        for serialized in (_serialize_vat_return(doc, etax_repo=etax_repo) for doc in docs)
        if _matches_filters(serialized, status_badge=status_badge)
    ]
    total = len(rows)
    start = max(page - 1, 0) * page_size
    end = start + page_size
    paged = rows[start:end]
    return {
        "data": paged,
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _build_listing_summary(rows),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("vat_return:read"))])
def get_vat_return(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    etax_repo = _get_etax_invoice_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    return _serialize_vat_return(doc, etax_repo=etax_repo)


@router.get("/{doc_id}/summary", dependencies=[Depends(require_permission("vat_return:read"))])
def get_vat_return_summary(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    return get_vat_return(doc_id, user)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("vat_return:update"))])
def update_vat_return(
    doc_id: str,
    body: VATReturnUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    etax_repo = _get_etax_invoice_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    check_draft_status(doc, "수정")
    update = body.model_dump(exclude_unset=True)
    if not update:
        return _serialize_vat_return(doc, etax_repo=etax_repo)
    if "output_tax" in update or "input_tax" in update:
        output_tax = _to_decimal(update.get("output_tax", doc.get("output_tax", 0)))
        input_tax = _to_decimal(update.get("input_tax", doc.get("input_tax", 0)))
        update["net_tax"] = output_tax - input_tax
        update["tax_amount"] = output_tax - input_tax
    repo.update_by_id(doc_id, update)
    updated = get_or_404(repo, doc_id, _NOT_FOUND)
    return _serialize_vat_return(updated, etax_repo=etax_repo)


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("vat_return:submit"))])
def submit_vat_return(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    etax_repo = _get_etax_invoice_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    check_draft_status(doc, "제출")
    filing_date = doc.get("filing_date") or _today()
    repo.update_by_id(doc_id, {"status": "submitted", "filing_date": filing_date})
    repo.submit(doc_id)
    submitted = get_or_404(repo, doc_id, _NOT_FOUND)
    submitted["status"] = "submitted"
    submitted["filing_date"] = filing_date
    submitted["docstatus"] = DocStatus.SUBMITTED
    return _serialize_vat_return(submitted, etax_repo=etax_repo)


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("vat_return:submit"))])
def cancel_vat_return(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    etax_repo = _get_etax_invoice_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    if int(doc.get("docstatus", DocStatus.DRAFT)) != DocStatus.SUBMITTED:
        raise_bad_request("제출된 문서만 취소할 수 있습니다")
    repo.update_by_id(doc_id, {"status": "cancelled"})
    repo.cancel(doc_id)
    cancelled = get_or_404(repo, doc_id, _NOT_FOUND)
    cancelled["status"] = "cancelled"
    cancelled["docstatus"] = DocStatus.CANCELLED
    return _serialize_vat_return(cancelled, etax_repo=etax_repo)


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("vat_return:delete"))]
)
def delete_vat_return(doc_id: str, user: CurrentUserDep) -> None:
    repo = _get_repo(user.tenant_id)
    delete_draft(repo, doc_id, _NOT_FOUND)
