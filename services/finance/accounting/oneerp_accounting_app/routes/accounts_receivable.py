"""매출채권(Accounts Receivable) 라우터 — 고객별 미수금 추적용 읽기 전용 뷰."""

from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found
from oneerp_core.permissions import require_permission

from ..services.accounts_receivable_service import (
    get_dunning_repo as _service_get_dunning_repo,
)
from ..services.accounts_receivable_service import (
    get_receivable_repo as _service_get_receivable_repo,
)

router = APIRouter(prefix="/api/v1/accounts-receivable", tags=["매출채권"])

_AGING_BUCKETS = ("current", "1-30", "31-60", "61-90", "91+")


def _get_repo(tenant_id: str):
    """매출채권 Repository를 서비스 레이어를 통해 획득한다 (OE002)."""
    return _service_get_receivable_repo(tenant_id)


def _get_dunning_repo(tenant_id: str):
    """독촉장 Repository를 서비스 레이어를 통해 획득한다 (OE002)."""
    return _service_get_dunning_repo(tenant_id)


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


def _build_dunning_index(dunning_docs: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """고객별 최신 독촉 상태를 인덱싱한다."""
    index: dict[str, dict[str, Any]] = {}
    for doc in dunning_docs:
        if int(doc.get("docstatus", 0)) == 2:
            continue
        customer = str(doc.get("customer") or "").strip()
        if not customer:
            continue

        current = index.setdefault(
            customer,
            {
                "latest_dunning_id": "",
                "latest_dunning_level": 0,
                "active_dunning_count": 0,
                "latest_dunning_date": None,
                "total_dunning_fee": Decimal(0),
            },
        )
        current["active_dunning_count"] += 1
        current["total_dunning_fee"] += _to_decimal(doc.get("dunning_fee", 0))

        dunning_date = _to_date(doc.get("dunning_date"))
        latest_date = current["latest_dunning_date"]
        if latest_date is None or (dunning_date is not None and dunning_date >= latest_date):
            current["latest_dunning_date"] = dunning_date
            current["latest_dunning_id"] = str(doc.get("_id") or "")
            current["latest_dunning_level"] = int(doc.get("dunning_level", 0) or 0)

    return index


def _resolve_collection_status(
    *,
    outstanding_amount: Decimal,
    overdue_days: int,
    latest_dunning_level: int,
) -> str:
    """수금 우선순위 상태를 계산한다."""
    if outstanding_amount <= 0:
        return "settled"
    if latest_dunning_level >= 2:
        return "critical_dunning"
    if latest_dunning_level == 1:
        return "dunning_in_progress"
    if overdue_days > 90:
        return "critical_overdue"
    if overdue_days > 0:
        return "overdue"
    return "current"


def _resolve_recommended_action(
    *,
    outstanding_amount: Decimal,
    overdue_days: int,
    latest_dunning_level: int,
) -> str:
    """현재 상태에서 사용자가 가장 먼저 해야 할 액션을 제안한다."""
    if outstanding_amount <= 0:
        return "none"
    if latest_dunning_level >= 2:
        return "call_customer"
    if latest_dunning_level == 1:
        return "review_dunning"
    if overdue_days > 0:
        return "create_dunning"
    return "monitor"


def _build_available_actions(
    *,
    outstanding_amount: Decimal,
    overdue_days: int,
    latest_dunning_level: int,
) -> list[str]:
    """매출채권 화면에서 바로 이어갈 수 있는 액션을 노출한다."""
    actions = ["open_invoice"]
    if outstanding_amount > 0:
        actions.append("register_payment")
    if latest_dunning_level > 0:
        actions.append("view_dunning_history")
    elif overdue_days > 0:
        actions.append("create_dunning")
    return actions


def _serialize_receivable(
    doc: dict[str, Any],
    *,
    as_of_date: date,
    dunning_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """매출채권 문서를 응답용 페이로드로 정규화한다."""
    payload = dict(doc)
    due_date = _to_date(payload.get("due_date"))
    outstanding_amount = _to_decimal(payload.get("outstanding_amount", 0))
    overdue_days = 0
    if due_date is not None and outstanding_amount > 0:
        overdue_days = max((as_of_date - due_date).days, 0)

    customer = str(payload.get("customer") or "").strip()
    dunning_summary = dunning_index.get(customer, {})
    latest_dunning_level = int(dunning_summary.get("latest_dunning_level", 0) or 0)

    payload["due_date"] = due_date.isoformat() if due_date is not None else None
    payload["outstanding_amount"] = float(outstanding_amount)
    payload["overdue_days"] = overdue_days
    payload["aging_bucket"] = _resolve_aging_bucket(overdue_days, payload.get("aging_bucket", ""))
    payload["latest_dunning_level"] = latest_dunning_level
    payload["latest_dunning_id"] = dunning_summary.get("latest_dunning_id", "")
    payload["collection_status"] = _resolve_collection_status(
        outstanding_amount=outstanding_amount,
        overdue_days=overdue_days,
        latest_dunning_level=latest_dunning_level,
    )
    payload["recommended_action"] = _resolve_recommended_action(
        outstanding_amount=outstanding_amount,
        overdue_days=overdue_days,
        latest_dunning_level=latest_dunning_level,
    )
    payload["available_actions"] = _build_available_actions(
        outstanding_amount=outstanding_amount,
        overdue_days=overdue_days,
        latest_dunning_level=latest_dunning_level,
    )
    return payload


def _matches_filters(
    doc: dict[str, Any],
    *,
    customer: str | None,
    due_date_from: date | None,
    due_date_to: date | None,
    overdue_only: bool,
    min_overdue_days: int | None,
    max_overdue_days: int | None,
) -> bool:
    """고객/만기/연체 조건으로 매출채권을 필터링한다."""
    if customer and doc.get("customer") != customer:
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
    return not (max_overdue_days is not None and overdue_days > max_overdue_days)


def _build_customer_breakdown(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """고객별 미수금 현황을 합산한다."""
    grouped: dict[str, dict[str, Any]] = {}
    for doc in docs:
        customer = str(doc.get("customer") or "").strip()
        if not customer:
            continue
        current = grouped.setdefault(
            customer,
            {
                "customer": customer,
                "customer_name": str(doc.get("customer_name") or ""),
                "invoice_count": 0,
                "overdue_invoice_count": 0,
                "outstanding_amount": Decimal(0),
                "overdue_outstanding": Decimal(0),
                "max_overdue_days": 0,
                "latest_dunning_level": int(doc.get("latest_dunning_level", 0) or 0),
                "latest_dunning_id": str(doc.get("latest_dunning_id") or ""),
            },
        )
        outstanding_amount = _to_decimal(doc.get("outstanding_amount", 0))
        overdue_days = int(doc.get("overdue_days", 0))
        current["invoice_count"] += 1
        current["outstanding_amount"] += outstanding_amount
        current["max_overdue_days"] = max(current["max_overdue_days"], overdue_days)
        if overdue_days > 0 and outstanding_amount > 0:
            current["overdue_invoice_count"] += 1
            current["overdue_outstanding"] += outstanding_amount
        if int(doc.get("latest_dunning_level", 0) or 0) >= current["latest_dunning_level"]:
            current["latest_dunning_level"] = int(doc.get("latest_dunning_level", 0) or 0)
            current["latest_dunning_id"] = str(doc.get("latest_dunning_id") or "")

    customer_breakdown: list[dict[str, Any]] = []
    for current in grouped.values():
        status = _resolve_collection_status(
            outstanding_amount=current["outstanding_amount"],
            overdue_days=current["max_overdue_days"],
            latest_dunning_level=current["latest_dunning_level"],
        )
        action = _resolve_recommended_action(
            outstanding_amount=current["outstanding_amount"],
            overdue_days=current["max_overdue_days"],
            latest_dunning_level=current["latest_dunning_level"],
        )
        customer_breakdown.append(
            {
                "customer": current["customer"],
                "customer_name": current["customer_name"],
                "invoice_count": current["invoice_count"],
                "overdue_invoice_count": current["overdue_invoice_count"],
                "outstanding_amount": float(current["outstanding_amount"]),
                "overdue_outstanding": float(current["overdue_outstanding"]),
                "max_overdue_days": current["max_overdue_days"],
                "collection_status": status,
                "recommended_action": action,
                "latest_dunning_level": current["latest_dunning_level"],
                "latest_dunning_id": current["latest_dunning_id"],
            }
        )

    customer_breakdown.sort(
        key=lambda item: (
            -item["overdue_outstanding"],
            -item["max_overdue_days"],
            item["customer"],
        )
    )
    return customer_breakdown


def _build_summary(docs: list[dict[str, Any]]) -> dict[str, Any]:
    """필터링된 매출채권의 aging 요약을 계산한다."""
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

    customer_breakdown = _build_customer_breakdown(docs)
    priority_customer_count = sum(
        1 for item in customer_breakdown if item["collection_status"] not in {"current", "settled"}
    )

    return {
        "total_outstanding": float(total_outstanding),
        "overdue_outstanding": float(overdue_outstanding),
        "overdue_count": overdue_count,
        "aging_buckets": bucket_summary,
        "customer_count": len(customer_breakdown),
        "priority_customer_count": priority_customer_count,
        "customer_breakdown": customer_breakdown,
    }


def _serialize_dunning_summary(summary: dict[str, Any]) -> dict[str, Any]:
    """독촉 요약을 JSON 직렬화 가능한 형태로 변환한다."""
    latest_dunning_date = summary.get("latest_dunning_date")
    return {
        "latest_dunning_id": summary.get("latest_dunning_id", ""),
        "latest_dunning_level": int(summary.get("latest_dunning_level", 0) or 0),
        "active_dunning_count": int(summary.get("active_dunning_count", 0) or 0),
        "latest_dunning_date": latest_dunning_date.isoformat() if latest_dunning_date else None,
        "total_dunning_fee": float(summary.get("total_dunning_fee", Decimal(0))),
    }


@router.get("", dependencies=[Depends(require_permission("accounts_receivable:read"))])
def 매출채권_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    *,
    customer: Annotated[str | None, Query(description="고객 필터")] = None,
    due_date_from: Annotated[date | None, Query(description="만기일 시작")] = None,
    due_date_to: Annotated[date | None, Query(description="만기일 종료")] = None,
    overdue_only: Annotated[bool, Query(description="연체 채권만 조회")] = False,
    min_overdue_days: Annotated[int | None, Query(ge=0, description="최소 연체일")] = None,
    max_overdue_days: Annotated[int | None, Query(ge=0, description="최대 연체일")] = None,
    as_of_date: Annotated[date | None, Query(description="연체 계산 기준일")] = None,
    voucher_no: Annotated[str | None, Query(description="원천 전표 번호 필터")] = None,
) -> dict[str, Any]:
    """매출채권 현황을 고객/만기/연체 기준으로 조회하고 고객별 요약을 반환한다."""
    repo = _get_repo(user.tenant_id)
    dunning_repo = _get_dunning_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if customer:
        query["customer"] = customer
    if voucher_no:
        query["invoice_id"] = voucher_no

    base_date = as_of_date or datetime.now(UTC).date()
    docs = list(repo.find_many(query, sort=[("due_date", 1), ("created_at", -1)]))
    dunning_query: dict[str, Any] = {}
    if customer:
        dunning_query["customer"] = customer
    dunning_docs = list(
        dunning_repo.find_many(dunning_query, limit=50000, sort=[("dunning_date", -1)])
    )
    dunning_index = _build_dunning_index(dunning_docs)

    serialized = [
        _serialize_receivable(doc, as_of_date=base_date, dunning_index=dunning_index)
        for doc in docs
    ]
    filtered = [
        doc
        for doc in serialized
        if _matches_filters(
            doc,
            customer=customer,
            due_date_from=due_date_from,
            due_date_to=due_date_to,
            overdue_only=overdue_only,
            min_overdue_days=min_overdue_days,
            max_overdue_days=max_overdue_days,
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
        "summary": _build_summary(filtered),
        "as_of_date": base_date.isoformat(),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("accounts_receivable:read"))])
def 매출채권_상세(
    doc_id: str,
    user: CurrentUserDep,
    *,
    as_of_date: Annotated[date | None, Query(description="연체 계산 기준일")] = None,
) -> dict[str, Any]:
    """매출채권 단건 상세와 독촉·후속 액션 맥락을 반환한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("매출채권 항목을 찾을 수 없습니다")
    assert doc is not None

    customer = str(doc.get("customer") or "").strip()
    customer_docs = list(
        repo.find_many(
            {"customer": customer}, limit=50000, sort=[("due_date", 1), ("created_at", -1)]
        )
    )
    dunning_docs = list(
        _get_dunning_repo(user.tenant_id).find_many(
            {"customer": customer},
            limit=50000,
            sort=[("dunning_date", -1)],
        )
    )
    dunning_index = _build_dunning_index(dunning_docs)
    base_date = as_of_date or datetime.now(UTC).date()

    serialized_customer_docs = [
        _serialize_receivable(item, as_of_date=base_date, dunning_index=dunning_index)
        for item in customer_docs
    ]
    customer_breakdown = _build_customer_breakdown(serialized_customer_docs)
    customer_summary = next(
        (item for item in customer_breakdown if item["customer"] == customer),
        {
            "customer": customer,
            "customer_name": str(doc.get("customer_name") or ""),
            "invoice_count": 0,
            "overdue_invoice_count": 0,
            "outstanding_amount": 0.0,
            "overdue_outstanding": 0.0,
            "max_overdue_days": 0,
            "collection_status": "current",
            "recommended_action": "monitor",
            "latest_dunning_level": 0,
            "latest_dunning_id": "",
        },
    )
    payload = _serialize_receivable(doc, as_of_date=base_date, dunning_index=dunning_index)
    payload["dunning_summary"] = _serialize_dunning_summary(dunning_index.get(customer, {}))
    payload["customer_summary"] = customer_summary
    payload["as_of_date"] = base_date.isoformat()
    return payload
