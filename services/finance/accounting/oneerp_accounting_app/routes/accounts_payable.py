"""매입채무(Accounts Payable) 라우터 — 공급업체별 미지급금 추적용 읽기 전용 뷰."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

router = APIRouter(prefix="/api/v1/accounts-payable", tags=["매입채무"])

_COLLECTION = "accounts_payable"
_AGING_BUCKETS = ("current", "1-30", "31-60", "61-90", "91+")
_DUE_SOON_DAYS = 7


def _get_repo(tenant_id: str) -> Repository:
    """매입채무 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _to_date(value: Any) -> date | None:
    """문자열/날짜를 date로 정규화한다."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _to_decimal(value: Any) -> Decimal:
    """숫자/문자열을 Decimal로 정규화한다."""
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _resolve_aging_bucket(overdue_days: int, fallback: str = "") -> str:
    """연체일 기준 aging bucket을 계산한다."""
    if overdue_days <= 0:
        return "current"
    if overdue_days <= 30:
        return "1-30"
    if overdue_days <= 60:
        return "31-60"
    if overdue_days <= 90:
        return "61-90"
    return fallback or "91+"


def _resolve_status_badge(
    *,
    outstanding_amount: Decimal,
    overdue_days: int,
    due_date: date | None,
    as_of_date: date,
) -> str:
    """지급 우선순위 배지를 계산한다."""
    if outstanding_amount <= 0:
        return "settled"
    if overdue_days > 30:
        return "critical_overdue"
    if overdue_days > 0:
        return "overdue"
    if due_date is not None and 0 <= (due_date - as_of_date).days <= _DUE_SOON_DAYS:
        return "due_soon"
    return "current"


def _resolve_recommended_action(*, status_badge: str) -> str:
    """현재 상태에서 가장 먼저 해야 할 액션을 제안한다."""
    if status_badge == "settled":
        return "none"
    if status_badge in {"critical_overdue", "overdue"}:
        return "register_payment"
    if status_badge == "due_soon":
        return "create_payment_order"
    return "monitor"


def _build_available_actions(
    *,
    outstanding_amount: Decimal,
    status_badge: str,
) -> list[str]:
    """매입채무 화면에서 바로 이어갈 수 있는 액션을 노출한다."""
    actions = ["open_purchase_invoice"]
    if outstanding_amount > 0:
        actions.append("register_payment")
    if status_badge in {"critical_overdue", "overdue", "due_soon"}:
        actions.append("create_payment_order")
    return actions


def _select_next_due_date(docs: list[dict[str, Any]], *, as_of_date: date) -> str | None:
    """다음 지급 예정일을 계산한다."""
    future_dates = sorted(
        due_date
        for doc in docs
        if _to_decimal(doc.get("outstanding_amount", 0)) > 0
        for due_date in [_to_date(doc.get("due_date"))]
        if due_date is not None and due_date >= as_of_date
    )
    if future_dates:
        return future_dates[0].isoformat()

    past_dates = sorted(
        due_date
        for doc in docs
        if _to_decimal(doc.get("outstanding_amount", 0)) > 0
        for due_date in [_to_date(doc.get("due_date"))]
        if due_date is not None
    )
    if past_dates:
        return past_dates[0].isoformat()
    return None


def _select_oldest_due_date(docs: list[dict[str, Any]]) -> str | None:
    """가장 오래된 만기일을 계산한다."""
    due_dates = sorted(
        due_date
        for doc in docs
        for due_date in [_to_date(doc.get("due_date"))]
        if due_date is not None
    )
    if not due_dates:
        return None
    return due_dates[0].isoformat()


def _serialize_payable(doc: dict[str, Any], *, as_of_date: date) -> dict[str, Any]:
    """매입채무 문서를 응답용 페이로드로 정규화한다."""
    payload = dict(doc)
    due_date = _to_date(payload.get("due_date"))
    outstanding_amount = _to_decimal(payload.get("outstanding_amount", 0))
    overdue_days = 0
    if due_date is not None and outstanding_amount > 0:
        overdue_days = max((as_of_date - due_date).days, 0)

    status_badge = _resolve_status_badge(
        outstanding_amount=outstanding_amount,
        overdue_days=overdue_days,
        due_date=due_date,
        as_of_date=as_of_date,
    )
    payload["supplier_name"] = str(payload.get("supplier_name") or payload.get("supplier") or "")
    payload["due_date"] = due_date.isoformat() if due_date is not None else None
    payload["outstanding_amount"] = float(outstanding_amount)
    payload["overdue_days"] = overdue_days
    payload["aging_bucket"] = _resolve_aging_bucket(overdue_days, payload.get("aging_bucket", ""))
    payload["status_badge"] = status_badge
    payload["recommended_action"] = _resolve_recommended_action(status_badge=status_badge)
    payload["available_actions"] = _build_available_actions(
        outstanding_amount=outstanding_amount,
        status_badge=status_badge,
    )
    return payload


def _matches_filters(
    doc: dict[str, Any],
    *,
    supplier: str | None,
    due_date_from: date | None,
    due_date_to: date | None,
    overdue_only: bool,
    min_overdue_days: int | None,
    max_overdue_days: int | None,
    status_badge: str | None,
) -> bool:
    """공급업체/만기/연체/배지 조건으로 매입채무를 필터링한다."""
    if supplier and doc.get("supplier") != supplier:
        return False

    due_date = _to_date(doc.get("due_date"))
    if due_date_from is not None and (due_date is None or due_date < due_date_from):
        return False
    if due_date_to is not None and (due_date is None or due_date > due_date_to):
        return False

    outstanding_amount = float(doc.get("outstanding_amount", 0))
    overdue_days = int(doc.get("overdue_days", 0))
    if overdue_only and not (outstanding_amount > 0 and overdue_days > 0):
        return False
    if min_overdue_days is not None and overdue_days < min_overdue_days:
        return False
    if max_overdue_days is not None and overdue_days > max_overdue_days:
        return False
    return not (status_badge and doc.get("status_badge") != status_badge)


def _build_supplier_breakdown(
    docs: list[dict[str, Any]], *, as_of_date: date
) -> list[dict[str, Any]]:
    """공급업체별 미지급금 현황을 합산한다."""
    grouped: dict[str, dict[str, Any]] = {}
    for doc in docs:
        supplier = str(doc.get("supplier") or "").strip()
        if not supplier:
            continue
        current = grouped.setdefault(
            supplier,
            {
                "supplier": supplier,
                "supplier_name": str(doc.get("supplier_name") or supplier),
                "invoice_count": 0,
                "overdue_invoice_count": 0,
                "outstanding_amount": Decimal(0),
                "overdue_outstanding": Decimal(0),
                "max_overdue_days": 0,
                "docs": [],
            },
        )
        outstanding_amount = _to_decimal(doc.get("outstanding_amount", 0))
        overdue_days = int(doc.get("overdue_days", 0))
        current["invoice_count"] += 1
        current["outstanding_amount"] += outstanding_amount
        current["max_overdue_days"] = max(current["max_overdue_days"], overdue_days)
        current["docs"].append(doc)
        if overdue_days > 0 and outstanding_amount > 0:
            current["overdue_invoice_count"] += 1
            current["overdue_outstanding"] += outstanding_amount

    supplier_breakdown: list[dict[str, Any]] = []
    for current in grouped.values():
        next_due_date = _select_next_due_date(current["docs"], as_of_date=as_of_date)
        status_badge = _resolve_status_badge(
            outstanding_amount=current["outstanding_amount"],
            overdue_days=current["max_overdue_days"],
            due_date=_to_date(next_due_date),
            as_of_date=as_of_date,
        )
        supplier_breakdown.append(
            {
                "supplier": current["supplier"],
                "supplier_name": current["supplier_name"],
                "invoice_count": current["invoice_count"],
                "overdue_invoice_count": current["overdue_invoice_count"],
                "outstanding_amount": float(current["outstanding_amount"]),
                "overdue_outstanding": float(current["overdue_outstanding"]),
                "max_overdue_days": current["max_overdue_days"],
                "next_due_date": next_due_date,
                "status_badge": status_badge,
                "recommended_action": _resolve_recommended_action(status_badge=status_badge),
            }
        )

    supplier_breakdown.sort(
        key=lambda item: (
            -item["overdue_outstanding"],
            -item["outstanding_amount"],
            item["supplier"],
        )
    )
    return supplier_breakdown


def _build_summary(docs: list[dict[str, Any]], *, as_of_date: date) -> dict[str, Any]:
    """필터링된 매입채무의 aging 요약을 계산한다."""
    bucket_summary = {bucket: {"count": 0, "amount": 0.0} for bucket in _AGING_BUCKETS}
    total_outstanding = Decimal(0)
    overdue_outstanding = Decimal(0)
    overdue_count = 0

    for doc in docs:
        outstanding_amount = _to_decimal(doc.get("outstanding_amount", 0))
        total_outstanding += outstanding_amount
        if outstanding_amount > 0 and int(doc.get("overdue_days", 0)) > 0:
            overdue_outstanding += outstanding_amount
            overdue_count += 1

        bucket = str(doc.get("aging_bucket") or "current")
        if bucket not in bucket_summary:
            bucket = "current"
        bucket_summary[bucket]["count"] += 1
        bucket_summary[bucket]["amount"] = round(
            bucket_summary[bucket]["amount"] + float(outstanding_amount),
            2,
        )

    supplier_breakdown = _build_supplier_breakdown(docs, as_of_date=as_of_date)
    priority_supplier_count = sum(
        1 for item in supplier_breakdown if item["status_badge"] not in {"current", "settled"}
    )

    return {
        "total_outstanding": float(total_outstanding),
        "overdue_outstanding": float(overdue_outstanding),
        "overdue_count": overdue_count,
        "aging_buckets": bucket_summary,
        "supplier_count": len(supplier_breakdown),
        "priority_supplier_count": priority_supplier_count,
        "supplier_breakdown": supplier_breakdown,
    }


def _build_payment_schedule_summary(
    docs: list[dict[str, Any]], *, as_of_date: date
) -> dict[str, Any]:
    """공급업체 단위 지급 일정 요약을 계산한다."""
    overdue_invoice_count = 0
    due_within_7_days_count = 0
    due_today_count = 0
    settled_invoice_count = 0
    overdue_outstanding = Decimal(0)
    total_outstanding = Decimal(0)

    for doc in docs:
        outstanding_amount = _to_decimal(doc.get("outstanding_amount", 0))
        due_date = _to_date(doc.get("due_date"))
        total_outstanding += outstanding_amount
        if outstanding_amount <= 0:
            settled_invoice_count += 1
            continue
        if due_date is None:
            continue
        delta_days = (due_date - as_of_date).days
        if delta_days < 0:
            overdue_invoice_count += 1
            overdue_outstanding += outstanding_amount
        elif delta_days == 0:
            due_today_count += 1
            due_within_7_days_count += 1
        elif delta_days <= _DUE_SOON_DAYS:
            due_within_7_days_count += 1

    return {
        "overdue_invoice_count": overdue_invoice_count,
        "due_within_7_days_count": due_within_7_days_count,
        "due_today_count": due_today_count,
        "settled_invoice_count": settled_invoice_count,
        "overdue_outstanding": float(overdue_outstanding),
        "total_outstanding": float(total_outstanding),
        "oldest_due_date": _select_oldest_due_date(docs),
        "next_due_date": _select_next_due_date(docs, as_of_date=as_of_date),
    }


@router.get("", dependencies=[Depends(require_permission("accounts_payable:read"))])
def 매입채무_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    *,
    supplier: Annotated[str | None, Query(description="공급업체 필터")] = None,
    due_date_from: Annotated[date | None, Query(description="만기일 시작")] = None,
    due_date_to: Annotated[date | None, Query(description="만기일 종료")] = None,
    overdue_only: Annotated[bool, Query(description="연체 채무만 조회")] = False,
    min_overdue_days: Annotated[int | None, Query(ge=0, description="최소 연체일")] = None,
    max_overdue_days: Annotated[int | None, Query(ge=0, description="최대 연체일")] = None,
    as_of_date: Annotated[date | None, Query(description="연체 기준일")] = None,
    voucher_no: Annotated[str | None, Query(description="원천 전표 번호 필터")] = None,
    status_badge: Annotated[str | None, Query(description="지급 우선순위 배지 필터")] = None,
) -> dict[str, Any]:
    """매입채무 현황을 공급업체/만기/연체 기준으로 조회하고 공급업체별 요약을 반환한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if supplier:
        query["supplier"] = supplier
    if voucher_no:
        query["invoice_id"] = voucher_no
    기준일 = as_of_date or datetime.now(UTC).date()
    docs = list(repo.find_many(query, sort=[("due_date", 1), ("created_at", -1)]))
    serialized = [_serialize_payable(doc, as_of_date=기준일) for doc in docs]
    filtered = [
        doc
        for doc in serialized
        if _matches_filters(
            doc,
            supplier=supplier,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            overdue_only=overdue_only,
            min_overdue_days=min_overdue_days,
            max_overdue_days=max_overdue_days,
            status_badge=status_badge,
        )
    ]
    total_count = len(filtered)
    skip = (page - 1) * page_size
    paged_docs = filtered[skip : skip + page_size]
    return {
        "data": paged_docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "summary": _build_summary(filtered, as_of_date=기준일),
        "as_of_date": 기준일.isoformat(),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("accounts_payable:read"))])
def 매입채무_상세(
    doc_id: str,
    user: CurrentUserDep,
    *,
    as_of_date: Annotated[date | None, Query(description="연체 기준일")] = None,
) -> dict[str, Any]:
    """매입채무 상세와 공급업체별 지급 일정 요약을 반환한다."""
    repo = _get_repo(user.tenant_id)
    기준일 = as_of_date or datetime.now(UTC).date()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found(f"매입채무를 찾을 수 없습니다: {doc_id}")
    assert doc is not None
    payable = _serialize_payable(doc, as_of_date=기준일)
    supplier = str(payable.get("supplier") or "").strip()
    related_docs = list(
        repo.find_many(
            {"supplier": supplier}, limit=50000, sort=[("due_date", 1), ("created_at", -1)]
        )
    )
    related_serialized = [_serialize_payable(item, as_of_date=기준일) for item in related_docs]
    supplier_breakdown = _build_supplier_breakdown(related_serialized, as_of_date=기준일)
    supplier_summary = next(
        (item for item in supplier_breakdown if item["supplier"] == supplier),
        {
            "supplier": supplier,
            "supplier_name": str(payable.get("supplier_name") or supplier),
            "invoice_count": 0,
            "overdue_invoice_count": 0,
            "outstanding_amount": 0.0,
            "overdue_outstanding": 0.0,
            "max_overdue_days": 0,
            "next_due_date": None,
            "status_badge": "current",
            "recommended_action": "monitor",
        },
    )
    payable["supplier_summary"] = supplier_summary
    payable["payment_schedule_summary"] = _build_payment_schedule_summary(
        related_serialized,
        as_of_date=기준일,
    )
    return payable
