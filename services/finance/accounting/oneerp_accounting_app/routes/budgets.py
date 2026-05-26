"""예산(Budget) 워크벤치 라우터."""

from __future__ import annotations

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from oneerp_core.route_helpers import check_draft_status, delete_draft, get_or_404

from ..models.budget import Budget, BudgetCreate, BudgetUpdate

router = APIRouter(prefix="/api/v1/budgets", tags=["예산"])

_COLLECTION = "budgets"
_PREFIX = "BGT"
_NOT_FOUND = "예산을 찾을 수 없습니다"
_LIST_SORT = [("fiscal_year", -1), ("budget_name", 1), ("created_at", -1)]
_PAGE_LIMIT = 500


def _get_repo(tenant_id: str) -> Repository:
    """예산 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_budget_version_repo(tenant_id: str) -> Repository:
    """예산 버전 Repository를 반환한다."""
    return Repository("budget_versions", tenant_id=tenant_id)


def _get_budget_transfer_repo(tenant_id: str) -> Repository:
    """예산 이전 Repository를 반환한다."""
    return Repository("budget_transfers", tenant_id=tenant_id)


def _to_decimal(value: Any) -> Decimal:
    """응답/문서 숫자를 Decimal로 정규화한다."""
    if value in (None, ""):
        return Decimal(0)
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def _to_date(value: Any) -> date | None:
    """문자열/날짜 값을 date로 정규화한다."""
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value))


def _to_float(value: Decimal) -> float:
    """Decimal을 float 응답값으로 변환한다."""
    return float(value)


def _normalize_budget_name(doc: dict[str, Any]) -> str:
    """예산명을 보정한다."""
    budget_name = str(doc.get("budget_name") or "").strip()
    if budget_name:
        return budget_name
    fiscal_year = str(doc.get("fiscal_year") or "").strip()
    cost_center = str(doc.get("cost_center") or "").strip()
    if fiscal_year and cost_center:
        return f"{fiscal_year} {cost_center} 예산"
    if fiscal_year:
        return f"{fiscal_year} 예산"
    return str(doc.get("_id") or "예산")


def _quantize_percentage(value: Decimal) -> float:
    """비율을 소수 둘째 자리까지 고정한다."""
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _build_budget_usage_summary(doc: dict[str, Any]) -> dict[str, Any]:
    """예산/실적/잔여/집행률을 계산한다."""
    items = list(doc.get("items") or [])
    item_budget_total = sum((_to_decimal(item.get("budget_amount")) for item in items), Decimal(0))
    item_actual_total = sum((_to_decimal(item.get("actual_amount")) for item in items), Decimal(0))

    total_amount = _to_decimal(doc.get("budget_amount"))
    spent_amount = _to_decimal(doc.get("actual_amount"))
    if total_amount == 0 and item_budget_total > 0:
        total_amount = item_budget_total
    if spent_amount == 0 and item_actual_total > 0:
        spent_amount = item_actual_total

    remaining_amount = total_amount - spent_amount
    utilization_rate = Decimal(0)
    if total_amount > 0:
        utilization_rate = (spent_amount / total_amount) * Decimal(100)

    over_budget_item_count = 0
    for item in items:
        line_budget = _to_decimal(item.get("budget_amount"))
        line_actual = _to_decimal(item.get("actual_amount"))
        if line_budget > 0 and line_actual > line_budget:
            over_budget_item_count += 1

    return {
        "total_amount": _to_float(total_amount),
        "spent_amount": _to_float(spent_amount),
        "remaining_amount": _to_float(remaining_amount),
        "utilization_rate": _quantize_percentage(utilization_rate),
        "line_item_count": len(items),
        "over_budget_item_count": over_budget_item_count,
    }


def _build_version_summary(version_repo: Repository, budget_id: str) -> dict[str, Any]:
    """예산 버전 요약을 계산한다."""
    versions = version_repo.find_many(
        {"budget_id": budget_id},
        limit=200,
        sort=[("version_no", -1), ("created_at", -1)],
    )
    current_version = next((item for item in versions if item.get("is_current")), None)
    return {
        "version_count": len(versions),
        "approved_version_count": sum(1 for item in versions if item.get("status") == "approved"),
        "locked_version_count": sum(1 for item in versions if item.get("status") == "locked"),
        "current_version_no": current_version.get("version_no") if current_version else None,
        "current_version_name": current_version.get("version_name") if current_version else None,
    }


def _build_transfer_summary(transfer_repo: Repository, budget_id: str) -> dict[str, Any]:
    """예산 이전 요약을 계산한다."""
    transfers = transfer_repo.find_many(
        {
            "$or": [
                {"from_budget_id": budget_id},
                {"to_budget_id": budget_id},
            ]
        },
        limit=200,
        sort=[("transfer_date", -1), ("created_at", -1)],
    )
    latest_transfer_date = None
    if transfers:
        latest_transfer_date = _to_date(transfers[0].get("transfer_date"))

    outbound = sum(
        (
            _to_decimal(item.get("transfer_amount"))
            for item in transfers
            if item.get("from_budget_id") == budget_id
        ),
        Decimal(0),
    )
    inbound = sum(
        (
            _to_decimal(item.get("transfer_amount"))
            for item in transfers
            if item.get("to_budget_id") == budget_id
        ),
        Decimal(0),
    )

    return {
        "pending_transfer_count": sum(
            1 for item in transfers if item.get("status") in {"draft", "approved"}
        ),
        "executed_transfer_count": sum(1 for item in transfers if item.get("status") == "executed"),
        "outbound_transfer_amount": _to_float(outbound),
        "inbound_transfer_amount": _to_float(inbound),
        "latest_transfer_date": latest_transfer_date.isoformat()
        if latest_transfer_date is not None
        else None,
    }


def _resolve_status_badge(
    doc: dict[str, Any],
    usage_summary: dict[str, Any],
    transfer_summary: dict[str, Any],
) -> str:
    """예산 통제 상태를 배지 문자열로 변환한다."""
    docstatus = int(doc.get("docstatus", DocStatus.DRAFT))
    if docstatus == DocStatus.CANCELLED:
        return "cancelled"
    if docstatus == DocStatus.DRAFT:
        return "draft"
    if usage_summary["remaining_amount"] < 0:
        return "over_budget"
    if usage_summary["utilization_rate"] >= 90:
        return "near_limit"
    if transfer_summary["pending_transfer_count"] > 0:
        return "transfer_pending"
    return "within_budget"


def _resolve_recommended_action(
    status_badge: str,
    version_summary: dict[str, Any],
) -> str:
    """상태에 맞는 후속 액션을 반환한다."""
    if status_badge == "draft":
        return "submit_budget"
    if status_badge == "over_budget":
        return "create_budget_transfer"
    if status_badge in {"near_limit", "transfer_pending"}:
        return "review_budget_transfer"
    if status_badge == "cancelled":
        return "none"
    if version_summary["version_count"] == 0:
        return "create_budget_version"
    return "monitor_budget"


def _build_available_actions(doc: dict[str, Any], status_badge: str) -> list[str]:
    """예산 워크벤치에서 노출할 액션 목록을 계산한다."""
    docstatus = int(doc.get("docstatus", DocStatus.DRAFT))
    actions: list[str] = []
    if docstatus == DocStatus.DRAFT:
        actions.extend(["edit", "submit"])
    if docstatus == DocStatus.SUBMITTED:
        actions.append("cancel")
    actions.extend(["open_budget_versions", "open_budget_transfers"])
    if status_badge in {"over_budget", "near_limit", "transfer_pending"}:
        actions.append("create_budget_transfer")
    return actions


def _serialize_budget(
    doc: dict[str, Any],
    *,
    version_repo: Repository,
    transfer_repo: Repository,
) -> dict[str, Any]:
    """예산 문서를 워크벤치 응답으로 직렬화한다."""
    payload = dict(doc)
    payload["budget_name"] = _normalize_budget_name(doc)
    usage_summary = _build_budget_usage_summary(doc)
    version_summary = _build_version_summary(version_repo, str(doc["_id"]))
    transfer_summary = _build_transfer_summary(transfer_repo, str(doc["_id"]))
    status_badge = _resolve_status_badge(doc, usage_summary, transfer_summary)

    payload["budget_amount"] = usage_summary["total_amount"]
    payload["actual_amount"] = usage_summary["spent_amount"]
    payload["total_amount"] = usage_summary["total_amount"]
    payload["spent_amount"] = usage_summary["spent_amount"]
    payload["remaining_amount"] = usage_summary["remaining_amount"]
    payload["budget_usage_summary"] = usage_summary
    payload["version_summary"] = version_summary
    payload["transfer_summary"] = transfer_summary
    payload["status_badge"] = status_badge
    payload["recommended_action"] = _resolve_recommended_action(status_badge, version_summary)
    payload["available_actions"] = _build_available_actions(doc, status_badge)
    return payload


def _build_list_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """목록 상단 워크벤치 요약을 계산한다."""
    return {
        "draft_count": sum(1 for row in rows if row.get("docstatus") == DocStatus.DRAFT),
        "submitted_count": sum(1 for row in rows if row.get("docstatus") == DocStatus.SUBMITTED),
        "cancelled_count": sum(1 for row in rows if row.get("docstatus") == DocStatus.CANCELLED),
        "over_budget_count": sum(1 for row in rows if row.get("status_badge") == "over_budget"),
        "near_limit_count": sum(1 for row in rows if row.get("status_badge") == "near_limit"),
        "pending_transfer_count": sum(
            1 for row in rows if row["transfer_summary"]["pending_transfer_count"] > 0
        ),
        "total_amount": round(
            sum(row["budget_usage_summary"]["total_amount"] for row in rows),
            2,
        ),
        "spent_amount": round(
            sum(row["budget_usage_summary"]["spent_amount"] for row in rows),
            2,
        ),
        "remaining_amount": round(
            sum(row["budget_usage_summary"]["remaining_amount"] for row in rows),
            2,
        ),
    }


def _make_budget_payload(
    body: BudgetCreate | BudgetUpdate, *, fallback_name: str
) -> dict[str, Any]:
    """요청 바디를 저장용 payload로 정규화한다."""
    payload = body.model_dump(exclude_none=True)
    payload["budget_name"] = (
        str(payload.get("budget_name") or fallback_name).strip() or fallback_name
    )
    items = payload.get("items") or []
    payload["budget_amount"] = _to_decimal(payload.get("budget_amount"))
    payload["actual_amount"] = _to_decimal(payload.get("actual_amount"))
    if payload["budget_amount"] == 0:
        payload["budget_amount"] = sum(
            (_to_decimal(item.get("budget_amount")) for item in items),
            Decimal(0),
        )
    if payload["actual_amount"] == 0:
        payload["actual_amount"] = sum(
            (_to_decimal(item.get("actual_amount")) for item in items),
            Decimal(0),
        )
    return payload


@router.post("", status_code=201, dependencies=[Depends(require_permission("budget:create"))])
def 예산_생성(body: BudgetCreate, user: CurrentUserDep) -> dict[str, Any]:
    """예산을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    fallback_name = f"{body.fiscal_year} {body.cost_center} 예산".strip() or f"예산 {doc_id}"
    payload = _make_budget_payload(body, fallback_name=fallback_name)
    budget = Budget(
        _id=doc_id,
        tenant_id=user.tenant_id,
        budget_name=payload["budget_name"],
        fiscal_year=str(payload.get("fiscal_year") or ""),
        cost_center=str(payload.get("cost_center") or ""),
        budget_amount=_to_decimal(payload.get("budget_amount")),
        actual_amount=_to_decimal(payload.get("actual_amount")),
        items=list(payload.get("items") or []),
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(budget)
    created = budget.model_dump(by_alias=True, exclude_none=True)
    serialized = _serialize_budget(
        created,
        version_repo=_get_budget_version_repo(user.tenant_id),
        transfer_repo=_get_budget_transfer_repo(user.tenant_id),
    )
    serialized["id"] = doc_id
    return serialized


@router.get("", dependencies=[Depends(require_permission("budget:read"))])
def 예산_목록(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    fiscal_year: str | None = None,
    cost_center: str | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """예산 목록과 워크벤치 요약을 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if fiscal_year:
        query["fiscal_year"] = fiscal_year
    if cost_center:
        query["cost_center"] = cost_center
    docs = repo.find_many(query, limit=_PAGE_LIMIT, sort=_LIST_SORT)
    version_repo = _get_budget_version_repo(user.tenant_id)
    transfer_repo = _get_budget_transfer_repo(user.tenant_id)
    rows = [
        _serialize_budget(doc, version_repo=version_repo, transfer_repo=transfer_repo)
        for doc in docs
    ]
    if status_badge:
        rows = [row for row in rows if row["status_badge"] == status_badge]

    if page_size > 100:
        page_size = 100
    start = max(page - 1, 0) * page_size
    end = start + page_size
    return {
        "data": rows[start:end],
        "total": len(rows),
        "page": page,
        "page_size": page_size,
        "summary": _build_list_summary(rows),
    }


@router.get("/summary", dependencies=[Depends(require_permission("budget:read"))])
def 예산_워크벤치_요약(
    user: CurrentUserDep,
    fiscal_year: str | None = None,
    cost_center: str | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """예산 워크벤치 요약만 조회한다."""
    payload = 예산_목록(
        user=user,
        page=1,
        page_size=100,
        fiscal_year=fiscal_year,
        cost_center=cost_center,
        status_badge=status_badge,
    )
    return payload["summary"]


@router.get("/{doc_id}", dependencies=[Depends(require_permission("budget:read"))])
def 예산_상세(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """예산 상세와 버전/이전 요약을 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    return _serialize_budget(
        doc,
        version_repo=_get_budget_version_repo(user.tenant_id),
        transfer_repo=_get_budget_transfer_repo(user.tenant_id),
    )


@router.put("/{doc_id}", dependencies=[Depends(require_permission("budget:write"))])
def 예산_수정(doc_id: str, body: BudgetUpdate, user: CurrentUserDep) -> dict[str, Any]:
    """예산을 수정한다. 초안 상태에서만 허용한다."""
    repo = _get_repo(user.tenant_id)
    existing = get_or_404(repo, doc_id, _NOT_FOUND)
    check_draft_status(existing, "수정")
    update_data = _make_budget_payload(
        body,
        fallback_name=_normalize_budget_name(existing),
    )
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    updated = {**existing, **update_data}
    return _serialize_budget(
        updated,
        version_repo=_get_budget_version_repo(user.tenant_id),
        transfer_repo=_get_budget_transfer_repo(user.tenant_id),
    )


@router.post("/{doc_id}/submit", dependencies=[Depends(require_permission("budget:submit"))])
def 예산_제출(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """초안 예산을 제출한다."""
    repo = _get_repo(user.tenant_id)
    existing = get_or_404(repo, doc_id, _NOT_FOUND)
    check_draft_status(existing, "제출")
    repo.submit(doc_id)
    submitted = {**existing, "docstatus": DocStatus.SUBMITTED}
    return _serialize_budget(
        submitted,
        version_repo=_get_budget_version_repo(user.tenant_id),
        transfer_repo=_get_budget_transfer_repo(user.tenant_id),
    )


@router.post("/{doc_id}/cancel", dependencies=[Depends(require_permission("budget:cancel"))])
def 예산_취소(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """제출된 예산을 취소한다."""
    repo = _get_repo(user.tenant_id)
    existing = get_or_404(repo, doc_id, _NOT_FOUND)
    if existing.get("docstatus") != DocStatus.SUBMITTED:
        msg = "제출된 문서만 취소할 수 있습니다"
        raise ValueError(msg)
    repo.cancel(doc_id)
    cancelled = {**existing, "docstatus": DocStatus.CANCELLED}
    return _serialize_budget(
        cancelled,
        version_repo=_get_budget_version_repo(user.tenant_id),
        transfer_repo=_get_budget_transfer_repo(user.tenant_id),
    )


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("budget:delete"))]
)
def 예산_삭제(doc_id: str, user: CurrentUserDep) -> None:
    """예산을 삭제한다. 초안 상태에서만 허용한다."""
    repo = _get_repo(user.tenant_id)
    delete_draft(repo, doc_id, _NOT_FOUND)
