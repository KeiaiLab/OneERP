"""회계기간(Accounting Period) 워크벤치 라우터."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError, raise_bad_request
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from pydantic import BaseModel

from ..models.accounting_period import (
    AccountingPeriod,
    AccountingPeriodCreate,
    AccountingPeriodUpdate,
)
from ..services.period_closing_service import PeriodClosingService

router = APIRouter(prefix="/api/v1/accounting-periods", tags=["회계기간"])

_COLLECTION = "accounting_periods"
_PREFIX = "APD"
_NOT_FOUND = "회계기간을 찾을 수 없습니다"
_PAGE_LIMIT = 500
_today_fn = date.today


class AccountingPeriodCloseRequest(BaseModel):
    """회계기간 마감 요청."""

    closing_account: str
    remarks: str = ""


def _today() -> date:
    return _today_fn()


def _get_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_fiscal_year_repo(tenant_id: str) -> Repository:
    return Repository("fiscal_years", tenant_id=tenant_id)


def _get_journal_entry_repo(tenant_id: str) -> Repository:
    return Repository("journal_entries", tenant_id=tenant_id)


def _get_period_closing_service(tenant_id: str) -> PeriodClosingService:
    return PeriodClosingService(tenant_id=tenant_id)


def _to_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _get_or_404(repo: Repository, doc_id: str) -> dict[str, Any]:
    doc = repo.find_by_id(doc_id)
    if doc is None:
        raise OneERPError(status_code=404, error="not_found", detail=_NOT_FOUND)
    return doc


def _validate_fiscal_year(fy_repo: Repository, fiscal_year_id: str) -> dict[str, Any] | None:
    if not fiscal_year_id:
        return None
    fiscal_year = fy_repo.find_by_id(fiscal_year_id)
    if fiscal_year is None:
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="회계연도를 찾을 수 없습니다",
        )
    return fiscal_year


def _normalize_scope_summary(doc: dict[str, Any]) -> dict[str, Any]:
    start_date = _to_date(doc.get("start_date"))
    end_date = _to_date(doc.get("end_date"))
    today = _today()
    is_current = bool(start_date and end_date and start_date <= today <= end_date)
    is_future = bool(start_date and start_date > today)
    is_past = bool(end_date and end_date < today)
    day_count = 0
    if start_date and end_date:
        day_count = (end_date - start_date).days + 1
    return {
        "company": doc.get("company", ""),
        "fiscal_year": doc.get("fiscal_year", ""),
        "day_count": day_count,
        "is_current": is_current,
        "is_future": is_future,
        "is_past": is_past,
    }


def _normalize_close_validation(service: PeriodClosingService, period_id: str) -> dict[str, Any]:
    result = service.validate_period_closeable(period_id)
    return {
        "closeable": bool(result.get("closeable")),
        "draft_count": int(result.get("draft_count", 0)),
        "submitted_count": int(result.get("submitted_count", 0)),
        "total_entries": int(result.get("total_entries", 0)),
    }


def _resolve_status_badge(
    doc: dict[str, Any],
    scope_summary: dict[str, Any],
    close_validation_summary: dict[str, Any],
    fiscal_year: dict[str, Any] | None,
) -> str:
    status = str(doc.get("status") or "open")
    fiscal_year_closed = bool(fiscal_year and fiscal_year.get("is_closed"))
    if status == "closed" and fiscal_year_closed:
        return "year_closed"
    if status == "closed":
        return "closed_reopenable"
    if scope_summary["is_future"]:
        return "future_open"
    if scope_summary["is_current"]:
        return "current_open"
    if close_validation_summary["closeable"]:
        return "close_ready"
    return "close_blocked"


def _resolve_recommended_action(status_badge: str) -> str:
    if status_badge == "close_ready":
        return "close_period"
    if status_badge == "close_blocked":
        return "review_draft_entries"
    if status_badge == "closed_reopenable":
        return "reopen_period"
    if status_badge == "year_closed":
        return "review_fiscal_year_closing"
    if status_badge == "future_open":
        return "monitor_period_start"
    return "monitor_current_period"


def _build_available_actions(status_badge: str) -> list[str]:
    actions = ["edit", "open_journal_entries", "validate_close"]
    if status_badge == "close_ready":
        actions.append("close")
    elif status_badge == "closed_reopenable":
        actions.append("reopen")
    return actions


def _serialize_period(
    doc: dict[str, Any],
    *,
    service: PeriodClosingService,
    fiscal_year: dict[str, Any] | None,
) -> dict[str, Any]:
    payload = dict(doc)
    scope_summary = _normalize_scope_summary(doc)
    close_validation_summary = _normalize_close_validation(service, str(doc["_id"]))
    status_badge = _resolve_status_badge(doc, scope_summary, close_validation_summary, fiscal_year)
    payload["period_scope_summary"] = scope_summary
    payload["close_validation_summary"] = close_validation_summary
    payload["status_badge"] = status_badge
    payload["recommended_action"] = _resolve_recommended_action(status_badge)
    payload["available_actions"] = _build_available_actions(status_badge)
    if fiscal_year is not None:
        payload["fiscal_year_closed"] = bool(fiscal_year.get("is_closed"))
        payload["fiscal_year_name"] = fiscal_year.get("year_name", "")
    return payload


def _build_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "open_count": sum(1 for row in rows if row.get("status") == "open"),
        "closed_count": sum(1 for row in rows if row.get("status") == "closed"),
        "current_period_count": sum(
            1 for row in rows if row["period_scope_summary"].get("is_current")
        ),
        "close_ready_count": sum(1 for row in rows if row.get("status_badge") == "close_ready"),
        "close_blocked_count": sum(1 for row in rows if row.get("status_badge") == "close_blocked"),
        "reopenable_count": sum(
            1 for row in rows if row.get("status_badge") == "closed_reopenable"
        ),
        "total_draft_entries": sum(
            int(row["close_validation_summary"].get("draft_count", 0)) for row in rows
        ),
    }


def _matches_filters(doc: dict[str, Any], *, status_badge: str | None) -> bool:
    return not (status_badge and doc.get("status_badge") != status_badge)


def _ensure_period_deletable(
    doc: dict[str, Any],
    *,
    fiscal_year: dict[str, Any] | None,
    journal_repo: Repository,
) -> None:
    if str(doc.get("status") or "open") == "closed":
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="마감된 회계기간은 삭제할 수 없습니다",
        )
    if fiscal_year and fiscal_year.get("is_closed"):
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="결산된 회계연도에 속한 회계기간은 삭제할 수 없습니다",
        )
    start_date = _to_date(doc.get("start_date"))
    end_date = _to_date(doc.get("end_date"))
    linked_journals = journal_repo.find_many(
        {"posting_date": {"$gte": start_date, "$lte": end_date}},
        limit=1,
    )
    if linked_journals:
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="분개전표가 연결된 회계기간은 삭제할 수 없습니다",
        )


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(require_permission("accounting_period:create"))],
)
def create_accounting_period(body: AccountingPeriodCreate, user: CurrentUserDep) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    fy_repo = _get_fiscal_year_repo(user.tenant_id)
    _validate_fiscal_year(fy_repo, body.fiscal_year)

    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    period = AccountingPeriod(
        _id=doc_id,
        tenant_id=user.tenant_id,
        period_name=body.period_name,
        start_date=body.start_date,
        end_date=body.end_date,
        company=body.company,
        status=body.status,
        fiscal_year=body.fiscal_year,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(period)
    service = _get_period_closing_service(user.tenant_id)
    created = _get_or_404(repo, doc_id)
    payload = _serialize_period(
        created,
        service=service,
        fiscal_year=_validate_fiscal_year(fy_repo, created.get("fiscal_year", "")),
    )
    payload["id"] = doc_id
    return payload


@router.get("", dependencies=[Depends(require_permission("accounting_period:read"))])
def list_accounting_periods(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    status_badge: str | None = None,
) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    fy_repo = _get_fiscal_year_repo(user.tenant_id)
    service = _get_period_closing_service(user.tenant_id)
    docs = repo.find_many(
        limit=_PAGE_LIMIT,
        sort=[("start_date", -1), ("period_name", -1), ("created_at", -1)],
    )
    enriched = [
        _serialize_period(
            doc,
            service=service,
            fiscal_year=_validate_fiscal_year(fy_repo, doc.get("fiscal_year", "")),
        )
        for doc in docs
    ]
    filtered = [doc for doc in enriched if _matches_filters(doc, status_badge=status_badge)]
    skip = max(page - 1, 0) * page_size
    return {
        "data": filtered[skip : skip + page_size],
        "total": len(filtered),
        "page": page,
        "page_size": page_size,
        "summary": _build_summary(filtered),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("accounting_period:read"))])
def get_accounting_period(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    fy_repo = _get_fiscal_year_repo(user.tenant_id)
    service = _get_period_closing_service(user.tenant_id)
    doc = _get_or_404(repo, doc_id)
    return _serialize_period(
        doc,
        service=service,
        fiscal_year=_validate_fiscal_year(fy_repo, doc.get("fiscal_year", "")),
    )


@router.get(
    "/{doc_id}/summary",
    dependencies=[Depends(require_permission("accounting_period:read"))],
)
def get_accounting_period_summary(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    return get_accounting_period(doc_id, user)


@router.put(
    "/{doc_id}",
    dependencies=[Depends(require_permission("accounting_period:update"))],
)
def update_accounting_period(
    doc_id: str,
    body: AccountingPeriodUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    fy_repo = _get_fiscal_year_repo(user.tenant_id)
    existing = _get_or_404(repo, doc_id)
    payload = body.model_dump(exclude_none=True)
    fiscal_year_id = payload.get("fiscal_year", existing.get("fiscal_year", ""))
    _validate_fiscal_year(fy_repo, str(fiscal_year_id or ""))
    payload["updated_by"] = user.sub
    repo.update_by_id(doc_id, payload)
    service = _get_period_closing_service(user.tenant_id)
    updated = _get_or_404(repo, doc_id)
    return _serialize_period(
        updated,
        service=service,
        fiscal_year=_validate_fiscal_year(fy_repo, updated.get("fiscal_year", "")),
    )


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("accounting_period:delete"))],
)
def delete_accounting_period(doc_id: str, user: CurrentUserDep) -> None:
    repo = _get_repo(user.tenant_id)
    fy_repo = _get_fiscal_year_repo(user.tenant_id)
    journal_repo = _get_journal_entry_repo(user.tenant_id)
    doc = _get_or_404(repo, doc_id)
    fiscal_year = _validate_fiscal_year(fy_repo, doc.get("fiscal_year", ""))
    _ensure_period_deletable(doc, fiscal_year=fiscal_year, journal_repo=journal_repo)
    repo.delete_by_id(doc_id)


@router.get(
    "/{doc_id}/close-validation",
    dependencies=[Depends(require_permission("accounting_period:read"))],
)
def get_close_validation(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    service = _get_period_closing_service(user.tenant_id)
    return _normalize_close_validation(service, doc_id)


@router.post(
    "/{doc_id}/close",
    dependencies=[Depends(require_permission("accounting_period:update"))],
)
def close_accounting_period(
    doc_id: str,
    body: AccountingPeriodCloseRequest,
    user: CurrentUserDep,
) -> dict[str, Any]:
    service = _get_period_closing_service(user.tenant_id)
    result = service.close_period(
        period_id=doc_id,
        closing_account=body.closing_account,
        remarks=body.remarks,
    )
    repo = _get_repo(user.tenant_id)
    fy_repo = _get_fiscal_year_repo(user.tenant_id)
    updated = _get_or_404(repo, doc_id)
    payload = _serialize_period(
        updated,
        service=service,
        fiscal_year=_validate_fiscal_year(fy_repo, updated.get("fiscal_year", "")),
    )
    payload["close_result"] = result
    return payload


@router.post(
    "/{doc_id}/reopen",
    dependencies=[Depends(require_permission("accounting_period:update"))],
)
def reopen_accounting_period(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    fy_repo = _get_fiscal_year_repo(user.tenant_id)
    doc = _get_or_404(repo, doc_id)
    if str(doc.get("status") or "open") != "closed":
        raise_bad_request("마감된 회계기간만 재개할 수 있습니다")
    fiscal_year = _validate_fiscal_year(fy_repo, doc.get("fiscal_year", ""))
    if fiscal_year and fiscal_year.get("is_closed"):
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="결산된 회계연도에 속한 회계기간은 재개할 수 없습니다",
        )
    repo.update_by_id(doc_id, {"status": "open", "updated_by": user.sub})
    service = _get_period_closing_service(user.tenant_id)
    updated = _get_or_404(repo, doc_id)
    return _serialize_period(updated, service=service, fiscal_year=fiscal_year)
