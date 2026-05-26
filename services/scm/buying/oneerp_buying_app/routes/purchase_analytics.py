"""구매 분석(Purchase Analytics) 워크벤치 라우터."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any, Literal

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

router = APIRouter(prefix="/api/v1/purchase-analytics", tags=["구매 분석"])

_PURCHASE_ORDER_COLLECTION = "purchase_orders"
_PURCHASE_INVOICE_COLLECTION = "purchase_invoices"
_SCORECARD_COLLECTION = "supplier_scorecards"

GroupBy = Literal["period", "supplier", "item"]


def _get_purchase_order_repo(tenant_id: str) -> Repository:
    """구매주문 저장소를 반환한다."""
    return Repository(_PURCHASE_ORDER_COLLECTION, tenant_id=tenant_id)


def _get_purchase_invoice_repo(tenant_id: str) -> Repository:
    """구매송장 저장소를 반환한다."""
    return Repository(_PURCHASE_INVOICE_COLLECTION, tenant_id=tenant_id)


def _get_scorecard_repo(tenant_id: str) -> Repository:
    """공급업체 평가 저장소를 반환한다."""
    return Repository(_SCORECARD_COLLECTION, tenant_id=tenant_id)


def _to_decimal(value: Any) -> Decimal:
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _normalize_date(value: Any) -> date | None:
    if value in (None, ""):
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


def _month_key(value: Any) -> str:
    normalized = _normalize_date(value)
    if not normalized:
        return ""
    return normalized.strftime("%Y-%m")


def _is_submitted(document: dict[str, Any]) -> bool:
    return document.get("docstatus") in {DocStatus.SUBMITTED, 1, "submitted", "Submitted"}


def _line_qty(item: dict[str, Any]) -> Decimal:
    return _to_decimal(item.get("qty", 0))


def _line_amount(item: dict[str, Any]) -> Decimal:
    amount = _to_decimal(item.get("amount", 0))
    if amount:
        return amount
    return _line_qty(item) * _to_decimal(item.get("rate", 0))


def _remaining_order_qty(document: dict[str, Any]) -> Decimal:
    remaining = Decimal(0)
    for item in document.get("items", []) or []:
        if not isinstance(item, dict):
            continue
        qty = _line_qty(item)
        received_qty = _to_decimal(item.get("received_qty", 0))
        remaining += max(qty - received_qty, Decimal(0))
    return remaining


def _is_overdue_payable(document: dict[str, Any], *, today: date) -> bool:
    due_date = _normalize_date(document.get("due_date"))
    outstanding_amount = _to_decimal(document.get("outstanding_amount", 0))
    return bool(due_date and due_date < today and outstanding_amount > 0)


def _load_submitted_purchase_orders(
    tenant_id: str,
    *,
    period_from: date | None,
    period_to: date | None,
    supplier_id: str | None,
    item_code: str | None,
) -> list[dict[str, Any]]:
    """필터에 맞는 제출 구매주문을 로드한다."""
    documents = _get_purchase_order_repo(tenant_id).find_many(
        limit=5000,
        sort=[("transaction_date", -1)],
    )
    matched: list[dict[str, Any]] = []
    for document in documents:
        if not _is_submitted(document):
            continue
        transaction_date = _normalize_date(document.get("transaction_date"))
        if period_from and (not transaction_date or transaction_date < period_from):
            continue
        if period_to and (not transaction_date or transaction_date > period_to):
            continue
        if supplier_id and str(document.get("supplier_id") or "") != supplier_id:
            continue
        items = list(document.get("items") or [])
        if item_code and not any(
            isinstance(item, dict) and item.get("item_code") == item_code for item in items
        ):
            continue
        matched.append(document)
    return matched


def _load_submitted_purchase_invoices(
    tenant_id: str,
    *,
    period_from: date | None,
    period_to: date | None,
    supplier_id: str | None,
    item_code: str | None,
) -> list[dict[str, Any]]:
    """필터에 맞는 제출 구매송장을 로드한다."""
    documents = _get_purchase_invoice_repo(tenant_id).find_many(
        limit=5000,
        sort=[("posting_date", -1)],
    )
    matched: list[dict[str, Any]] = []
    for document in documents:
        if not _is_submitted(document):
            continue
        posting_date = _normalize_date(document.get("posting_date"))
        if period_from and (not posting_date or posting_date < period_from):
            continue
        if period_to and (not posting_date or posting_date > period_to):
            continue
        if supplier_id and str(document.get("supplier_id") or "") != supplier_id:
            continue
        items = list(document.get("items") or [])
        if item_code and not any(
            isinstance(item, dict) and item.get("item_code") == item_code for item in items
        ):
            continue
        matched.append(document)
    return matched


def _load_latest_scorecards(tenant_id: str) -> dict[str, dict[str, Any]]:
    """공급업체별 최신 평가를 로드한다."""
    scorecards = _get_scorecard_repo(tenant_id).find_many(limit=5000, sort=[("created_at", -1)])
    latest_by_supplier: dict[str, dict[str, Any]] = {}
    for scorecard in scorecards:
        supplier_id = str(scorecard.get("supplier") or "")
        if supplier_id and supplier_id not in latest_by_supplier:
            latest_by_supplier[supplier_id] = scorecard
    return latest_by_supplier


def _build_purchase_trend(
    purchase_orders: list[dict[str, Any]],
    purchase_invoices: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    monthly: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {
            "ordered_amount": Decimal(0),
            "invoiced_amount": Decimal(0),
            "qty": Decimal(0),
        }
    )
    for document in purchase_orders:
        month = _month_key(document.get("transaction_date"))
        if not month:
            continue
        monthly[month]["ordered_amount"] += _to_decimal(document.get("grand_total", 0))
        monthly[month]["qty"] += sum(
            _line_qty(item) for item in document.get("items", []) or [] if isinstance(item, dict)
        )
    for document in purchase_invoices:
        month = _month_key(document.get("posting_date"))
        if not month:
            continue
        monthly[month]["invoiced_amount"] += _to_decimal(document.get("grand_total", 0))
    return [
        {
            "period": period,
            "ordered_amount": float(values["ordered_amount"]),
            "invoiced_amount": float(values["invoiced_amount"]),
            "qty": float(values["qty"]),
        }
        for period, values in sorted(monthly.items())
    ]


def _build_supplier_mix(
    purchase_orders: list[dict[str, Any]],
    purchase_invoices: list[dict[str, Any]],
    latest_scorecards: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}
    total_spend = Decimal(0)
    for document in purchase_orders:
        supplier_id = str(document.get("supplier_id") or "")
        if not supplier_id:
            continue
        supplier_name = document.get("supplier_name") or supplier_id
        record = totals.setdefault(
            supplier_id,
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "purchase_order_amount": Decimal(0),
                "purchase_invoice_amount": Decimal(0),
                "outstanding_amount": Decimal(0),
                "latest_scorecard_total": 0.0,
            },
        )
        record["purchase_order_amount"] += _to_decimal(document.get("grand_total", 0))
    for document in purchase_invoices:
        supplier_id = str(document.get("supplier_id") or "")
        if not supplier_id:
            continue
        supplier_name = document.get("supplier_name") or supplier_id
        record = totals.setdefault(
            supplier_id,
            {
                "supplier_id": supplier_id,
                "supplier_name": supplier_name,
                "purchase_order_amount": Decimal(0),
                "purchase_invoice_amount": Decimal(0),
                "outstanding_amount": Decimal(0),
                "latest_scorecard_total": 0.0,
            },
        )
        record["purchase_invoice_amount"] += _to_decimal(document.get("grand_total", 0))
        record["outstanding_amount"] += _to_decimal(document.get("outstanding_amount", 0))
    rows = list(totals.values())
    for row in rows:
        scorecard = latest_scorecards.get(row["supplier_id"])
        if scorecard:
            row["latest_scorecard_total"] = float(_to_decimal(scorecard.get("total_score", 0)))
        row["spend_amount"] = max(row["purchase_invoice_amount"], row["purchase_order_amount"])
        total_spend += row["spend_amount"]
    rows.sort(key=lambda row: (-row["spend_amount"], row["supplier_name"]))
    return [
        {
            "supplier_id": row["supplier_id"],
            "supplier_name": row["supplier_name"],
            "purchase_order_amount": float(row["purchase_order_amount"]),
            "purchase_invoice_amount": float(row["purchase_invoice_amount"]),
            "outstanding_amount": float(row["outstanding_amount"]),
            "latest_scorecard_total": row["latest_scorecard_total"],
            "share_ratio": round(float(row["spend_amount"] / total_spend), 4)
            if total_spend
            else 0.0,
        }
        for row in rows[:5]
    ]


def _build_item_mix(
    purchase_orders: list[dict[str, Any]],
    purchase_invoices: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    totals: dict[str, dict[str, Any]] = {}
    total_spend = Decimal(0)
    for document in purchase_orders:
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
                    "item_name": item.get("item_name") or item_code,
                    "purchase_order_amount": Decimal(0),
                    "purchase_invoice_amount": Decimal(0),
                    "qty": Decimal(0),
                },
            )
            record["purchase_order_amount"] += _line_amount(item)
            record["qty"] += _line_qty(item)
    for document in purchase_invoices:
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
                    "item_name": item.get("item_name") or item_code,
                    "purchase_order_amount": Decimal(0),
                    "purchase_invoice_amount": Decimal(0),
                    "qty": Decimal(0),
                },
            )
            record["purchase_invoice_amount"] += _line_amount(item)
    rows = list(totals.values())
    for row in rows:
        row["spend_amount"] = max(row["purchase_invoice_amount"], row["purchase_order_amount"])
        total_spend += row["spend_amount"]
    rows.sort(key=lambda row: (-row["spend_amount"], row["item_code"]))
    return [
        {
            "item_code": row["item_code"],
            "item_name": row["item_name"],
            "purchase_order_amount": float(row["purchase_order_amount"]),
            "purchase_invoice_amount": float(row["purchase_invoice_amount"]),
            "qty": float(row["qty"]),
            "share_ratio": round(float(row["spend_amount"] / total_spend), 4)
            if total_spend
            else 0.0,
        }
        for row in rows[:5]
    ]


def _payable_status(document: dict[str, Any], *, today: date) -> str:
    outstanding_amount = _to_decimal(document.get("outstanding_amount", 0))
    if outstanding_amount <= 0:
        return "settled"
    if _is_overdue_payable(document, today=today):
        return "overdue"
    return "open"


def _build_payable_pipeline(purchase_invoices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    today = datetime.now(UTC).date()
    counts: dict[str, int] = defaultdict(int)
    amounts: dict[str, Decimal] = defaultdict(Decimal)
    for document in purchase_invoices:
        status = _payable_status(document, today=today)
        counts[status] += 1
        amount_key = "grand_total" if status == "settled" else "outstanding_amount"
        amounts[status] += _to_decimal(document.get(amount_key, 0))
    order = {"overdue": 0, "open": 1, "settled": 2}
    return [
        {"status": status, "count": counts[status], "amount": float(amounts[status])}
        for status in sorted(counts, key=lambda key: order.get(key, 99))
    ]


def _group_period_rows(
    purchase_orders: list[dict[str, Any]],
    purchase_invoices: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "purchase_order_amount": Decimal(0),
            "purchase_invoice_amount": Decimal(0),
            "qty": Decimal(0),
            "purchase_order_ids": set(),
            "purchase_invoice_ids": set(),
            "supplier_ids": set(),
        }
    )
    for document in purchase_orders:
        period = _month_key(document.get("transaction_date"))
        if not period:
            continue
        record = grouped[period]
        record["purchase_order_amount"] += _to_decimal(document.get("grand_total", 0))
        record["qty"] += sum(
            _line_qty(item) for item in document.get("items", []) or [] if isinstance(item, dict)
        )
        record["purchase_order_ids"].add(str(document.get("_id") or ""))
        if document.get("supplier_id"):
            record["supplier_ids"].add(str(document.get("supplier_id")))
    for document in purchase_invoices:
        period = _month_key(document.get("posting_date"))
        if not period:
            continue
        record = grouped[period]
        record["purchase_invoice_amount"] += _to_decimal(document.get("grand_total", 0))
        record["purchase_invoice_ids"].add(str(document.get("_id") or ""))
        if document.get("supplier_id"):
            record["supplier_ids"].add(str(document.get("supplier_id")))
    rows = [
        {
            "group_key": period,
            "group_label": period,
            "purchase_order_amount": values["purchase_order_amount"],
            "purchase_invoice_amount": values["purchase_invoice_amount"],
            "qty": values["qty"],
            "purchase_order_count": len(values["purchase_order_ids"]),
            "purchase_invoice_count": len(values["purchase_invoice_ids"]),
            "supplier_count": len(values["supplier_ids"]),
        }
        for period, values in grouped.items()
    ]

    def _row_spend_amount(row: dict[str, Any]) -> Decimal:
        """기간별 합산 지출 금액을 계산한다."""
        return _to_decimal(row["purchase_invoice_amount"]) + _to_decimal(
            row["purchase_order_amount"]
        )

    rows.sort(
        key=lambda row: (
            -_row_spend_amount(row),
            row["group_key"],
        )
    )
    if not rows:
        return []
    top_spend = max((_row_spend_amount(row) for row in rows), default=Decimal(0))
    avg_spend = sum((_row_spend_amount(row) for row in rows), Decimal(0)) / Decimal(len(rows))
    serialized: list[dict[str, Any]] = []
    for row in rows:
        spend_amount = _row_spend_amount(row)
        if spend_amount == top_spend and spend_amount > 0:
            badge = "spend_peak"
            recommended_action = "review_supplier_capacity"
        elif spend_amount >= avg_spend and spend_amount > 0:
            badge = "spend_active"
            recommended_action = "review_purchase_mix"
        else:
            badge = "spend_watch"
            recommended_action = "investigate_spend_gap"
        serialized.append(
            {
                "id": f"PANA-PERIOD-{row['group_key']}",
                "group_by": "period",
                "group_key": row["group_key"],
                "group_label": row["group_label"],
                "purchase_order_amount": float(row["purchase_order_amount"]),
                "purchase_invoice_amount": float(row["purchase_invoice_amount"]),
                "total_qty": float(row["qty"]),
                "status_badge": badge,
                "recommended_action": recommended_action,
                "available_actions": [
                    "open_purchase_orders",
                    "open_purchase_invoices",
                    "review_supplier_scorecards",
                ],
                "summary": {
                    "purchase_order_count": row["purchase_order_count"],
                    "purchase_invoice_count": row["purchase_invoice_count"],
                    "supplier_count": row["supplier_count"],
                },
            }
        )
    return serialized


def _group_supplier_rows(
    purchase_orders: list[dict[str, Any]],
    purchase_invoices: list[dict[str, Any]],
    latest_scorecards: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    today = datetime.now(UTC).date()
    grouped: dict[str, dict[str, Any]] = {}
    for document in purchase_orders:
        supplier_id = str(document.get("supplier_id") or "")
        if not supplier_id:
            continue
        record = grouped.setdefault(
            supplier_id,
            {
                "supplier_id": supplier_id,
                "supplier_name": document.get("supplier_name") or supplier_id,
                "purchase_order_amount": Decimal(0),
                "purchase_invoice_amount": Decimal(0),
                "outstanding_amount": Decimal(0),
                "total_qty": Decimal(0),
                "purchase_order_count": 0,
                "purchase_invoice_count": 0,
                "overdue_payable_count": 0,
            },
        )
        record["purchase_order_amount"] += _to_decimal(document.get("grand_total", 0))
        record["purchase_order_count"] += 1
        record["total_qty"] += sum(
            _line_qty(item) for item in document.get("items", []) or [] if isinstance(item, dict)
        )
    for document in purchase_invoices:
        supplier_id = str(document.get("supplier_id") or "")
        if not supplier_id:
            continue
        record = grouped.setdefault(
            supplier_id,
            {
                "supplier_id": supplier_id,
                "supplier_name": document.get("supplier_name") or supplier_id,
                "purchase_order_amount": Decimal(0),
                "purchase_invoice_amount": Decimal(0),
                "outstanding_amount": Decimal(0),
                "total_qty": Decimal(0),
                "purchase_order_count": 0,
                "purchase_invoice_count": 0,
                "overdue_payable_count": 0,
            },
        )
        record["purchase_invoice_amount"] += _to_decimal(document.get("grand_total", 0))
        record["purchase_invoice_count"] += 1
        record["outstanding_amount"] += _to_decimal(document.get("outstanding_amount", 0))
        if _is_overdue_payable(document, today=today):
            record["overdue_payable_count"] += 1
    rows = list(grouped.values())
    if not rows:
        return []
    top_spend = max(
        max(row["purchase_invoice_amount"], row["purchase_order_amount"]) for row in rows
    )
    avg_spend = sum(
        max(row["purchase_invoice_amount"], row["purchase_order_amount"]) for row in rows
    ) / Decimal(len(rows))
    rows.sort(
        key=lambda row: (
            -max(row["purchase_invoice_amount"], row["purchase_order_amount"]),
            row["supplier_name"],
        )
    )
    serialized: list[dict[str, Any]] = []
    for row in rows:
        scorecard = latest_scorecards.get(row["supplier_id"])
        score = float(_to_decimal(scorecard.get("total_score", 0))) if scorecard else 0.0
        spend_amount = max(row["purchase_invoice_amount"], row["purchase_order_amount"])
        if row["overdue_payable_count"] > 0:
            badge = "payment_due"
            recommended_action = "review_payables"
        elif scorecard and score < 80:
            badge = "performance_watch"
            recommended_action = "review_scorecard"
        elif spend_amount == top_spend and spend_amount > 0:
            badge = "top_supplier"
            recommended_action = "negotiate_contract"
        elif spend_amount >= avg_spend and spend_amount > 0:
            badge = "active_supplier"
            recommended_action = "review_purchase_mix"
        else:
            badge = "supplier_watch"
            recommended_action = "review_supplier_mix"
        serialized.append(
            {
                "id": f"PANA-SUPPLIER-{row['supplier_id']}",
                "group_by": "supplier",
                "group_key": row["supplier_id"],
                "group_label": row["supplier_name"],
                "purchase_order_amount": float(row["purchase_order_amount"]),
                "purchase_invoice_amount": float(row["purchase_invoice_amount"]),
                "outstanding_amount": float(row["outstanding_amount"]),
                "total_qty": float(row["total_qty"]),
                "status_badge": badge,
                "recommended_action": recommended_action,
                "available_actions": [
                    "open_supplier",
                    "open_purchase_orders",
                    "open_purchase_invoices",
                    "review_supplier_scorecards",
                ],
                "summary": {
                    "purchase_order_count": row["purchase_order_count"],
                    "purchase_invoice_count": row["purchase_invoice_count"],
                    "overdue_payable_count": row["overdue_payable_count"],
                    "latest_scorecard_total": score,
                },
            }
        )
    return serialized


def _group_item_rows(
    purchase_orders: list[dict[str, Any]],
    purchase_invoices: list[dict[str, Any]],
    *,
    item_code: str | None,
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for document in purchase_orders:
        supplier_id = str(document.get("supplier_id") or "")
        for item in document.get("items", []) or []:
            if not isinstance(item, dict):
                continue
            current_item_code = str(item.get("item_code") or "")
            if not current_item_code or (item_code and current_item_code != item_code):
                continue
            record = grouped.setdefault(
                current_item_code,
                {
                    "item_code": current_item_code,
                    "item_name": item.get("item_name") or current_item_code,
                    "purchase_order_amount": Decimal(0),
                    "purchase_invoice_amount": Decimal(0),
                    "total_qty": Decimal(0),
                    "supplier_ids": set(),
                    "purchase_order_ids": set(),
                    "purchase_invoice_ids": set(),
                },
            )
            record["purchase_order_amount"] += _line_amount(item)
            record["total_qty"] += _line_qty(item)
            record["purchase_order_ids"].add(str(document.get("_id") or ""))
            if supplier_id:
                record["supplier_ids"].add(supplier_id)
    for document in purchase_invoices:
        supplier_id = str(document.get("supplier_id") or "")
        for item in document.get("items", []) or []:
            if not isinstance(item, dict):
                continue
            current_item_code = str(item.get("item_code") or "")
            if not current_item_code or (item_code and current_item_code != item_code):
                continue
            record = grouped.setdefault(
                current_item_code,
                {
                    "item_code": current_item_code,
                    "item_name": item.get("item_name") or current_item_code,
                    "purchase_order_amount": Decimal(0),
                    "purchase_invoice_amount": Decimal(0),
                    "total_qty": Decimal(0),
                    "supplier_ids": set(),
                    "purchase_order_ids": set(),
                    "purchase_invoice_ids": set(),
                },
            )
            record["purchase_invoice_amount"] += _line_amount(item)
            record["purchase_invoice_ids"].add(str(document.get("_id") or ""))
            if supplier_id:
                record["supplier_ids"].add(supplier_id)
    rows = list(grouped.values())
    if not rows:
        return []
    top_spend = max(
        max(row["purchase_invoice_amount"], row["purchase_order_amount"]) for row in rows
    )
    avg_qty = sum(row["total_qty"] for row in rows) / Decimal(len(rows))
    rows.sort(
        key=lambda row: (
            -max(row["purchase_invoice_amount"], row["purchase_order_amount"]),
            row["item_code"],
        )
    )
    serialized: list[dict[str, Any]] = []
    for row in rows:
        spend_amount = max(row["purchase_invoice_amount"], row["purchase_order_amount"])
        if spend_amount == top_spend and spend_amount > 0:
            badge = "top_spend_item"
            recommended_action = "review_cost_reduction"
        elif row["total_qty"] >= avg_qty and row["total_qty"] > 0:
            badge = "high_volume_item"
            recommended_action = "secure_supply"
        else:
            badge = "item_watch"
            recommended_action = "investigate_item_spend"
        serialized.append(
            {
                "id": f"PANA-ITEM-{row['item_code']}",
                "group_by": "item",
                "group_key": row["item_code"],
                "group_label": row["item_name"],
                "purchase_order_amount": float(row["purchase_order_amount"]),
                "purchase_invoice_amount": float(row["purchase_invoice_amount"]),
                "total_qty": float(row["total_qty"]),
                "status_badge": badge,
                "recommended_action": recommended_action,
                "available_actions": [
                    "open_item",
                    "open_purchase_orders",
                    "open_purchase_invoices",
                ],
                "summary": {
                    "supplier_count": len(row["supplier_ids"]),
                    "purchase_order_count": len(row["purchase_order_ids"]),
                    "purchase_invoice_count": len(row["purchase_invoice_ids"]),
                },
            }
        )
    return serialized


def _group_rows(
    purchase_orders: list[dict[str, Any]],
    purchase_invoices: list[dict[str, Any]],
    latest_scorecards: dict[str, dict[str, Any]],
    *,
    group_by: GroupBy,
    item_code: str | None,
) -> list[dict[str, Any]]:
    if group_by == "period":
        return _group_period_rows(purchase_orders, purchase_invoices)
    if group_by == "supplier":
        return _group_supplier_rows(purchase_orders, purchase_invoices, latest_scorecards)
    return _group_item_rows(purchase_orders, purchase_invoices, item_code=item_code)


def _build_summary(
    purchase_orders: list[dict[str, Any]],
    purchase_invoices: list[dict[str, Any]],
    supplier_mix: list[dict[str, Any]],
) -> dict[str, Any]:
    today = datetime.now(UTC).date()
    supplier_ids = {
        str(document.get("supplier_id") or "")
        for document in [*purchase_orders, *purchase_invoices]
        if str(document.get("supplier_id") or "")
    }
    return {
        "submitted_purchase_order_count": len(purchase_orders),
        "purchase_order_amount_total": float(
            sum(_to_decimal(document.get("grand_total", 0)) for document in purchase_orders)
        ),
        "submitted_purchase_invoice_count": len(purchase_invoices),
        "purchase_invoice_amount_total": float(
            sum(_to_decimal(document.get("grand_total", 0)) for document in purchase_invoices)
        ),
        "active_supplier_count": len(supplier_ids),
        "open_purchase_order_count": sum(
            1 for document in purchase_orders if _remaining_order_qty(document) > 0
        ),
        "overdue_payable_count": sum(
            1 for document in purchase_invoices if _is_overdue_payable(document, today=today)
        ),
        "best_supplier_name": supplier_mix[0]["supplier_name"] if supplier_mix else "",
        "best_supplier_amount": supplier_mix[0]["purchase_invoice_amount"] if supplier_mix else 0.0,
    }


def _dashboard_action(summary: dict[str, Any]) -> str:
    if summary["overdue_payable_count"] > 0:
        return "review_overdue_payables"
    if summary["open_purchase_order_count"] > 0:
        return "review_open_purchase_orders"
    if summary["submitted_purchase_invoice_count"] == 0:
        return "seed_first_purchase_invoice"
    return "review_top_suppliers"


@router.get("", dependencies=[Depends(require_permission("purchase_analytic:read"))])
def 구매분석_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    group_by: GroupBy = "period",
    period_from: date | None = None,
    period_to: date | None = None,
    supplier_id: str | None = None,
    item_code: str | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """구매 분석 KPI/차트/랭킹 워크벤치를 조회한다."""
    purchase_orders = _load_submitted_purchase_orders(
        user.tenant_id,
        period_from=period_from,
        period_to=period_to,
        supplier_id=supplier_id,
        item_code=item_code,
    )
    purchase_invoices = _load_submitted_purchase_invoices(
        user.tenant_id,
        period_from=period_from,
        period_to=period_to,
        supplier_id=supplier_id,
        item_code=item_code,
    )
    latest_scorecards = _load_latest_scorecards(user.tenant_id)
    group_rows = _group_rows(
        purchase_orders,
        purchase_invoices,
        latest_scorecards,
        group_by=group_by,
        item_code=item_code,
    )
    filtered_rows = [
        row for row in group_rows if not status_badge or row["status_badge"] == status_badge
    ]
    supplier_mix = _build_supplier_mix(purchase_orders, purchase_invoices, latest_scorecards)
    item_mix = _build_item_mix(purchase_orders, purchase_invoices)
    summary = _build_summary(purchase_orders, purchase_invoices, supplier_mix)
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
            "open_purchase_orders",
            "open_purchase_invoices",
            "open_suppliers",
            "review_supplier_scorecards",
        ],
        "charts": {
            "purchase_trend": _build_purchase_trend(purchase_orders, purchase_invoices),
            "supplier_mix": supplier_mix,
            "item_mix": item_mix,
            "payable_pipeline": _build_payable_pipeline(purchase_invoices),
        },
    }
