"""판매 분석(Sales Analytics) 워크벤치 라우터."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Literal

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.permissions import require_permission

from oneerp_selling_app.services.sales_analytics_service import SalesAnalyticsService

router = APIRouter(prefix="/api/v1/sales-analytics", tags=["판매 분석"])

GroupBy = Literal["period", "customer", "item"]


def _to_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _normalize_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.astimezone(UTC).date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value).date()
        except ValueError:
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
    return None


def _is_submitted(document: dict[str, Any]) -> bool:
    return document.get("docstatus") in {DocStatus.SUBMITTED, 1, "submitted", "Submitted"}


def _line_amount(item: dict[str, Any]) -> Decimal:
    amount = _to_decimal(item.get("amount", 0))
    if amount:
        return amount
    return _to_decimal(item.get("qty", 0)) * _to_decimal(item.get("rate", 0))


def _line_qty(item: dict[str, Any]) -> Decimal:
    return _to_decimal(item.get("qty", 0))


def _month_key(value: Any) -> str:
    normalized = _normalize_date(value)
    if not normalized:
        return ""
    return normalized.strftime("%Y-%m")


def _load_submitted_invoices(
    tenant_id: str,
    *,
    period_from: date | None,
    period_to: date | None,
    customer_id: str | None,
    item_code: str | None,
) -> list[dict[str, Any]]:
    """필터에 맞는 제출 판매송장을 로드한다."""
    invoices = SalesAnalyticsService(tenant_id).load_invoices()
    matched: list[dict[str, Any]] = []
    for document in invoices:
        if not _is_submitted(document):
            continue
        posting_date = _normalize_date(document.get("posting_date"))
        if period_from and (not posting_date or posting_date < period_from):
            continue
        if period_to and (not posting_date or posting_date > period_to):
            continue
        if customer_id and str(document.get("customer_id") or "") != customer_id:
            continue
        items = list(document.get("items") or [])
        if item_code and not any(
            item.get("item_code") == item_code for item in items if isinstance(item, dict)
        ):
            continue
        matched.append(document)
    return matched


def _quotation_status(document: dict[str, Any], *, today: date) -> str:
    if document.get("converted_to"):
        return "converted"
    if _is_submitted(document):
        valid_till = _normalize_date(document.get("valid_till"))
        if valid_till and valid_till < today:
            return "stale"
        return "submitted"
    return "draft"


def _build_quotation_pipeline(
    tenant_id: str,
    *,
    period_from: date | None,
    period_to: date | None,
    customer_id: str | None,
    item_code: str | None,
) -> tuple[list[dict[str, Any]], dict[str, int], dict[str, Decimal]]:
    """견적 파이프라인 현황을 집계한다."""
    today = datetime.now(UTC).date()
    quotations = SalesAnalyticsService(tenant_id).load_quotations()
    counts: dict[str, int] = defaultdict(int)
    amounts: dict[str, Decimal] = defaultdict(Decimal)
    for document in quotations:
        transaction_date = _normalize_date(document.get("transaction_date"))
        if period_from and (not transaction_date or transaction_date < period_from):
            continue
        if period_to and (not transaction_date or transaction_date > period_to):
            continue
        if customer_id and str(document.get("customer_id") or "") != customer_id:
            continue
        items = list(document.get("items") or [])
        if item_code and not any(
            item.get("item_code") == item_code for item in items if isinstance(item, dict)
        ):
            continue
        status = _quotation_status(document, today=today)
        counts[status] += 1
        amounts[status] += _to_decimal(document.get("grand_total", 0))
    order = {"draft": 0, "submitted": 1, "stale": 2, "converted": 3}
    rows = [
        {"status": status, "count": counts[status], "amount": float(amounts[status])}
        for status in sorted(counts, key=lambda key: order.get(key, 99))
    ]
    return rows, counts, amounts


def _build_period_chart(invoices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    monthly: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"amount": Decimal(0), "qty": Decimal(0)}
    )
    for document in invoices:
        month = _month_key(document.get("posting_date"))
        if not month:
            continue
        monthly[month]["amount"] += _to_decimal(document.get("grand_total", 0))
        monthly[month]["qty"] += sum(
            _line_qty(item) for item in document.get("items", []) if isinstance(item, dict)
        )
    return [
        {
            "period": period,
            "amount": float(values["amount"]),
            "qty": float(values["qty"]),
        }
        for period, values in sorted(monthly.items())
    ]


def _build_customer_mix(invoices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}
    grand_total = sum(_to_decimal(document.get("grand_total", 0)) for document in invoices)
    for document in invoices:
        customer_key = str(document.get("customer_id") or document.get("customer_name") or "")
        if not customer_key:
            continue
        record = totals.setdefault(
            customer_key,
            {
                "customer_id": str(document.get("customer_id") or ""),
                "customer_name": document.get("customer_name", customer_key),
                "amount": Decimal(0),
            },
        )
        record["amount"] += _to_decimal(document.get("grand_total", 0))
    rows = sorted(totals.values(), key=lambda row: (-row["amount"], row["customer_name"]))
    return [
        {
            "customer_id": row["customer_id"],
            "customer_name": row["customer_name"],
            "amount": float(row["amount"]),
            "share_ratio": round(float(row["amount"] / grand_total), 4) if grand_total else 0.0,
        }
        for row in rows[:5]
    ]


def _build_item_mix(invoices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}
    grand_total = sum(_to_decimal(document.get("grand_total", 0)) for document in invoices)
    for document in invoices:
        for item in document.get("items", []) or []:
            if not isinstance(item, dict):
                continue
            item_code = str(item.get("item_code") or "")
            if not item_code:
                continue
            record = totals.setdefault(
                item_code,
                {
                    "item_code": item_code,
                    "item_name": item.get("item_name", item_code),
                    "amount": Decimal(0),
                    "qty": Decimal(0),
                },
            )
            record["amount"] += _line_amount(item)
            record["qty"] += _line_qty(item)
    rows = sorted(totals.values(), key=lambda row: (-row["amount"], row["item_code"]))
    return [
        {
            "item_code": row["item_code"],
            "item_name": row["item_name"],
            "amount": float(row["amount"]),
            "qty": float(row["qty"]),
            "share_ratio": round(float(row["amount"] / grand_total), 4) if grand_total else 0.0,
        }
        for row in rows[:5]
    ]


def _row_badge(
    group_by: GroupBy,
    *,
    amount: Decimal,
    top_amount: Decimal,
    average_amount: Decimal,
) -> str:
    if group_by == "period":
        if amount == top_amount and amount > 0:
            return "period_peak"
        if amount >= average_amount and amount > 0:
            return "period_strong"
        return "period_watch"
    if group_by == "customer":
        if amount == top_amount and amount > 0:
            return "top_customer"
        if amount >= average_amount and amount > 0:
            return "growth_customer"
        return "customer_watch"
    if amount == top_amount and amount > 0:
        return "best_seller"
    if amount >= average_amount and amount > 0:
        return "high_volume_item"
    return "item_watch"


def _row_recommended_action(group_by: GroupBy, badge: str) -> str:
    if group_by == "period":
        if badge == "period_peak":
            return "review_capacity"
        if badge == "period_strong":
            return "expand_pipeline"
        return "follow_up_pipeline"
    if group_by == "customer":
        if badge == "top_customer":
            return "expand_account_plan"
        if badge == "growth_customer":
            return "protect_margin"
        return "review_account_pipeline"
    if badge == "best_seller":
        return "secure_stock"
    if badge == "high_volume_item":
        return "review_margin"
    return "plan_promotion"


def _row_available_actions(group_by: GroupBy, badge: str) -> list[str]:
    if group_by == "period":
        actions = ["open_sales_invoices", "open_quotations"]
        if badge == "period_peak":
            actions.append("review_capacity")
        return actions
    if group_by == "customer":
        actions = ["open_customer", "open_sales_invoices"]
        if badge in {"top_customer", "growth_customer"}:
            actions.append("review_margin")
        return actions
    actions = ["open_item", "open_sales_invoices"]
    if badge in {"best_seller", "high_volume_item"}:
        actions.append("review_margin")
    return actions


def _group_rows(
    invoices: list[dict[str, Any]],
    *,
    group_by: GroupBy,
    item_code: str | None,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    total_amount = sum(_to_decimal(document.get("grand_total", 0)) for document in invoices)
    for document in invoices:
        invoice_amount = _to_decimal(document.get("grand_total", 0))
        invoice_qty = sum(
            _line_qty(item) for item in document.get("items", []) if isinstance(item, dict)
        )
        if group_by == "period":
            group_key = _month_key(document.get("posting_date"))
            group_label = group_key
            targets = [("period", group_key, group_label, invoice_amount, invoice_qty)]
        elif group_by == "customer":
            group_key = str(document.get("customer_id") or document.get("customer_name") or "")
            group_label = document.get("customer_name") or group_key
            targets = [("customer", group_key, group_label, invoice_amount, invoice_qty)]
        else:
            targets = []
            for item in document.get("items", []) or []:
                if not isinstance(item, dict):
                    continue
                if item_code and item.get("item_code") != item_code:
                    continue
                group_key = str(item.get("item_code") or "")
                if not group_key:
                    continue
                group_label = item.get("item_name") or group_key
                targets.append(
                    ("item", group_key, group_label, _line_amount(item), _line_qty(item))
                )
        for _, group_key, group_label, amount, qty in targets:
            if not group_key:
                continue
            record = grouped.setdefault(
                group_key,
                {
                    "group_key": group_key,
                    "group_label": group_label,
                    "total_amount": Decimal(0),
                    "total_qty": Decimal(0),
                    "invoice_ids": set(),
                    "customer_ids": set(),
                },
            )
            record["total_amount"] += amount
            record["total_qty"] += qty
            record["invoice_ids"].add(str(document.get("_id") or ""))
            if document.get("customer_id"):
                record["customer_ids"].add(str(document.get("customer_id")))
    rows = list(grouped.values())
    if not rows:
        return []
    top_amount = max(row["total_amount"] for row in rows)
    average_amount = sum(row["total_amount"] for row in rows) / Decimal(len(rows))
    serialized = []
    for row in sorted(rows, key=lambda current: (-current["total_amount"], current["group_label"])):
        badge = _row_badge(
            group_by,
            amount=row["total_amount"],
            top_amount=top_amount,
            average_amount=average_amount,
        )
        serialized.append(
            {
                "id": f"SANA-{group_by.upper()}-{row['group_key']}",
                "group_by": group_by,
                "group_key": row["group_key"],
                "group_label": row["group_label"],
                "total_amount": float(row["total_amount"]),
                "total_qty": float(row["total_qty"]),
                "invoice_count": len(row["invoice_ids"]),
                "customer_count": len(row["customer_ids"]),
                "share_ratio": round(float(row["total_amount"] / total_amount), 4)
                if total_amount
                else 0.0,
                "status_badge": badge,
                "recommended_action": _row_recommended_action(group_by, badge),
                "available_actions": _row_available_actions(group_by, badge),
            }
        )
    return serialized


def _build_summary(
    invoices: list[dict[str, Any]],
    quotation_counts: dict[str, int],
    customer_mix: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "submitted_invoice_count": len(invoices),
        "invoice_amount_total": float(
            sum(_to_decimal(document.get("grand_total", 0)) for document in invoices)
        ),
        "active_customer_count": len(
            {
                str(document.get("customer_id") or "")
                for document in invoices
                if str(document.get("customer_id") or "")
            }
        ),
        "open_quotation_count": quotation_counts.get("draft", 0)
        + quotation_counts.get("submitted", 0)
        + quotation_counts.get("stale", 0),
        "stale_quotation_count": quotation_counts.get("stale", 0),
        "best_customer_name": customer_mix[0]["customer_name"] if customer_mix else "",
        "best_customer_amount": customer_mix[0]["amount"] if customer_mix else 0.0,
    }


def _dashboard_action(summary: dict[str, Any]) -> str:
    if summary["stale_quotation_count"] > 0:
        return "review_stale_quotations"
    if summary["submitted_invoice_count"] == 0:
        return "seed_first_invoice"
    if summary["open_quotation_count"] > 0:
        return "review_open_quotations"
    return "review_top_customers"


@router.get("", dependencies=[Depends(require_permission("sales_analytic:read"))])
def 판매분석_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    group_by: GroupBy = "period",
    period_from: date | None = None,
    period_to: date | None = None,
    customer_id: str | None = None,
    item_code: str | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """판매 분석 KPI/차트/랭킹 워크벤치를 조회한다."""
    invoices = _load_submitted_invoices(
        user.tenant_id,
        period_from=period_from,
        period_to=period_to,
        customer_id=customer_id,
        item_code=item_code,
    )
    group_rows = _group_rows(invoices, group_by=group_by, item_code=item_code)
    filtered_rows = [
        row for row in group_rows if not status_badge or row["status_badge"] == status_badge
    ]
    customer_mix = _build_customer_mix(invoices)
    item_mix = _build_item_mix(invoices)
    quotation_pipeline, quotation_counts, _ = _build_quotation_pipeline(
        user.tenant_id,
        period_from=period_from,
        period_to=period_to,
        customer_id=customer_id,
        item_code=item_code,
    )
    summary = _build_summary(invoices, quotation_counts, customer_mix)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": filtered_rows[start:end],
        "total": len(filtered_rows),
        "page": page,
        "page_size": page_size,
        "summary": summary,
        "recommended_action": _dashboard_action(summary),
        "available_actions": [
            "open_quotations",
            "open_sales_orders",
            "open_sales_invoices",
        ],
        "charts": {
            "sales_trend": _build_period_chart(invoices),
            "customer_mix": customer_mix,
            "item_mix": item_mix,
            "quotation_pipeline": quotation_pipeline,
        },
    }
