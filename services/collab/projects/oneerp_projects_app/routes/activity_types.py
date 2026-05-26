"""활동유형(ActivityType) 워크벤치 라우트."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, cast

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_conflict, raise_not_found, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.activity_type import ActivityType, ActivityTypeCreate, ActivityTypeUpdate

router = APIRouter(prefix="/api/v1/activity-types", tags=["활동유형"])

_COLLECTION = "activity_types"
_TIMESHEET_COLLECTION = "timesheets"
_PREFIX = "ATYP"
_NOT_FOUND_MESSAGE = "활동유형을 찾을 수 없습니다"


def _get_repo(tenant_id: str, collection: str = _COLLECTION) -> Repository:
    """현재 tenant에 바인딩된 저장소를 반환한다."""
    return Repository(collection, tenant_id=tenant_id)


def _with_public_id(document: dict[str, Any]) -> dict[str, Any]:
    """공개 응답용 `id`와 기본 마진 정보를 추가한다."""
    public = dict(document)
    if "_id" in public:
        public["id"] = public["_id"]
    margin_per_hour = Decimal(str(public.get("billing_rate", 0) or 0)) - Decimal(
        str(public.get("costing_rate", 0) or 0)
    )
    public["margin_per_hour"] = float(margin_per_hour)
    return public


def _sort_activity_types(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        documents,
        key=lambda document: (
            not bool(document.get("is_active", True)),
            str(document.get("activity_type", "")),
        ),
    )


def _normalize_date(value: Any) -> str | None:
    """문자열/날짜 값을 ISO 날짜 문자열로 맞춘다."""
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except ValueError:
        return None


def _collect_usage_summary(
    timesheet_documents: list[dict[str, Any]],
    activity_type_name: str,
) -> dict[str, Any]:
    """활동유형별 사용량과 미청구 시간을 계산한다."""
    if not activity_type_name:
        return {
            "timesheet_count": 0,
            "submitted_timesheet_count": 0,
            "active_project_count": 0,
            "total_logged_hours": 0.0,
            "unbilled_hours": 0.0,
            "last_used_date": None,
        }

    timesheet_ids: set[str] = set()
    submitted_timesheet_ids: set[str] = set()
    project_refs: set[str] = set()
    total_logged_hours = Decimal(0)
    unbilled_hours = Decimal(0)
    last_used_date: str | None = None

    for document in timesheet_documents:
        matching_logs = [
            log
            for log in list(document.get("time_logs", []) or [])
            if str(log.get("activity_type", "")).strip() == activity_type_name
        ]
        if not matching_logs:
            continue

        timesheet_id = str(document.get("_id", "")).strip()
        if timesheet_id:
            timesheet_ids.add(timesheet_id)
            if int(document.get("docstatus", 0) or 0) == 1:
                submitted_timesheet_ids.add(timesheet_id)

        is_submitted_unbilled = int(document.get("docstatus", 0) or 0) == 1 and not bool(
            document.get("billed", False)
        )
        for log in matching_logs:
            hours = Decimal(str(log.get("hours", 0) or 0))
            total_logged_hours += hours
            if is_submitted_unbilled:
                unbilled_hours += hours

            project_ref = str(log.get("project_ref", "")).strip()
            if project_ref:
                project_refs.add(project_ref)

            log_date = _normalize_date(log.get("date"))
            if log_date and (last_used_date is None or log_date > last_used_date):
                last_used_date = log_date

    return {
        "timesheet_count": len(timesheet_ids),
        "submitted_timesheet_count": len(submitted_timesheet_ids),
        "active_project_count": len(project_refs),
        "total_logged_hours": float(total_logged_hours),
        "unbilled_hours": float(unbilled_hours),
        "last_used_date": last_used_date,
    }


def _build_rate_summary(document: dict[str, Any], usage_summary: dict[str, Any]) -> dict[str, Any]:
    costing_rate = Decimal(str(document.get("costing_rate", 0) or 0))
    billing_rate = Decimal(str(document.get("billing_rate", 0) or 0))
    margin_per_hour = billing_rate - costing_rate
    expected_margin_amount = margin_per_hour * Decimal(
        str(usage_summary.get("total_logged_hours", 0) or 0)
    )
    return {
        "costing_rate": float(costing_rate),
        "billing_rate": float(billing_rate),
        "margin_per_hour": float(margin_per_hour),
        "expected_margin_amount": float(expected_margin_amount),
    }


def _build_status_badge(document: dict[str, Any], usage_summary: dict[str, Any]) -> str:
    is_active = bool(document.get("is_active", True))
    billing_rate = Decimal(str(document.get("billing_rate", 0) or 0))
    costing_rate = Decimal(str(document.get("costing_rate", 0) or 0))
    timesheet_count = int(usage_summary.get("timesheet_count", 0) or 0)

    if is_active and billing_rate < costing_rate:
        return "margin_watch"
    if not is_active and timesheet_count > 0:
        return "inactive_in_use"
    if not is_active:
        return "inactive_unused"
    if timesheet_count > 0:
        return "active_in_use"
    return "active_ready"


def _build_recommended_action(
    document: dict[str, Any],
    usage_summary: dict[str, Any],
    *,
    status_badge: str,
) -> str:
    if status_badge == "margin_watch":
        return "raise_billing_rate"
    if float(usage_summary.get("unbilled_hours", 0) or 0) > 0:
        return "review_unbilled_timesheets"
    if (
        not bool(document.get("is_active", True))
        and int(usage_summary.get("timesheet_count", 0) or 0) > 0
    ):
        return "review_historical_usage"
    if not bool(document.get("is_active", True)):
        return "delete_or_archive"
    return "keep_catalog_active"


def _build_available_actions(document: dict[str, Any], usage_summary: dict[str, Any]) -> list[str]:
    usage_count = int(usage_summary.get("timesheet_count", 0) or 0)
    if bool(document.get("is_active", True)):
        actions = ["edit"]
        if usage_count > 0:
            actions.append("open_timesheets")
        actions.append("deactivate")
        return actions

    actions = ["edit"]
    if usage_count > 0:
        actions.extend(["open_timesheets", "reactivate"])
    else:
        actions.extend(["reactivate", "delete"])
    return actions


def _decorate_activity_type(
    document: dict[str, Any],
    timesheet_documents: list[dict[str, Any]],
) -> dict[str, Any]:
    public = _with_public_id(document)
    usage_summary = _collect_usage_summary(
        timesheet_documents,
        str(public.get("activity_type", "")).strip(),
    )
    status_badge = _build_status_badge(public, usage_summary)
    public["usage_count"] = usage_summary["timesheet_count"]
    public["usage_summary"] = usage_summary
    public["rate_summary"] = _build_rate_summary(public, usage_summary)
    public["status_badge"] = status_badge
    public["recommended_action"] = _build_recommended_action(
        public,
        usage_summary,
        status_badge=status_badge,
    )
    public["available_actions"] = _build_available_actions(public, usage_summary)
    return public


def _summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = {
        "active_count": 0,
        "inactive_count": 0,
        "in_use_count": 0,
        "margin_watch_count": 0,
        "total_logged_hours": 0.0,
        "unbilled_hours": 0.0,
    }
    for row in rows:
        if bool(row.get("is_active", True)):
            summary["active_count"] += 1
        else:
            summary["inactive_count"] += 1
        if int(row.get("usage_summary", {}).get("timesheet_count", 0) or 0) > 0:
            summary["in_use_count"] += 1
        if row.get("status_badge") == "margin_watch":
            summary["margin_watch_count"] += 1
        summary["total_logged_hours"] += float(
            row.get("usage_summary", {}).get("total_logged_hours", 0.0) or 0.0
        )
        summary["unbilled_hours"] += float(
            row.get("usage_summary", {}).get("unbilled_hours", 0.0) or 0.0
        )
    summary["total_logged_hours"] = round(summary["total_logged_hours"], 2)
    summary["unbilled_hours"] = round(summary["unbilled_hours"], 2)
    return summary


def _ensure_unique_activity_type_name(
    repo: Repository,
    activity_type_name: str,
    *,
    exclude_id: str | None = None,
) -> None:
    matches = repo.find_many(query={"activity_type": activity_type_name}, limit=1000)
    for document in matches:
        if str(document.get("_id", "")) != str(exclude_id or ""):
            raise_conflict("동일한 활동유형명이 이미 존재합니다")


@router.post(
    "/", status_code=201, dependencies=[Depends(require_permission("activity_type:create"))]
)
async def create_activity_type(body: ActivityTypeCreate, user: CurrentUserDep) -> dict[str, Any]:
    """활동유형을 생성한다."""
    repo = _get_repo(user.tenant_id)
    payload = body.model_dump()
    _ensure_unique_activity_type_name(repo, payload["activity_type"])
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    document = ActivityType(
        _id=doc_id,
        tenant_id=user.tenant_id,
        created_by=user.sub,
        updated_by=user.sub,
        **payload,
    )
    repo.insert(document)
    return {
        "activity_type_id": doc_id,
        "id": doc_id,
        "message": "활동유형이 생성되었습니다",
        **payload,
    }


@router.get("/", dependencies=[Depends(require_permission("activity_type:read"))])
async def list_activity_types(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    *,
    is_active: bool | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """활동유형 목록을 워크벤치 요약과 함께 조회한다."""
    repo = _get_repo(user.tenant_id)
    timesheet_repo = _get_repo(user.tenant_id, collection=_TIMESHEET_COLLECTION)
    query: dict[str, Any] = {}
    if is_active is not None:
        query["is_active"] = is_active

    documents = _sort_activity_types(repo.find_many(query=query, limit=1000))
    timesheet_documents = timesheet_repo.find_many(limit=5000, sort=[("created_at", -1)])
    rows = [_decorate_activity_type(document, timesheet_documents) for document in documents]
    if status_badge:
        rows = [row for row in rows if row.get("status_badge") == status_badge]

    total = len(rows)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": rows[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _summarize(rows),
    }


@router.get("/catalog", dependencies=[Depends(require_permission("activity_type:read"))])
async def get_activity_type_catalog(user: CurrentUserDep) -> dict[str, Any]:
    """타임시트 입력 화면용 활성 활동유형 카탈로그를 반환한다."""
    repo = _get_repo(user.tenant_id)
    timesheet_repo = _get_repo(user.tenant_id, collection=_TIMESHEET_COLLECTION)
    documents = [
        document
        for document in _sort_activity_types(repo.find_many(limit=1000))
        if document.get("is_active", True)
    ]
    timesheet_documents = timesheet_repo.find_many(limit=5000, sort=[("created_at", -1)])
    data = [_decorate_activity_type(document, timesheet_documents) for document in documents]
    return {"data": data, "total": len(data)}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("activity_type:read"))])
async def get_activity_type(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """활동유형 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    document = cast("dict[str, Any]", document)
    timesheet_documents = _get_repo(user.tenant_id, collection=_TIMESHEET_COLLECTION).find_many(
        limit=5000,
        sort=[("created_at", -1)],
    )
    return _decorate_activity_type(document, timesheet_documents)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("activity_type:write"))])
async def update_activity_type(
    doc_id: str,
    body: ActivityTypeUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """활동유형을 수정한다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)
    document = cast("dict[str, Any]", document)

    update_data = body.model_dump(exclude_none=True)
    if activity_type_name := update_data.get("activity_type"):
        _ensure_unique_activity_type_name(repo, activity_type_name, exclude_id=doc_id)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    refreshed = {**document, **update_data}
    timesheet_documents = _get_repo(user.tenant_id, collection=_TIMESHEET_COLLECTION).find_many(
        limit=5000,
        sort=[("created_at", -1)],
    )
    return _decorate_activity_type(refreshed, timesheet_documents)


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("activity_type:delete"))],
)
async def delete_activity_type(doc_id: str, user: CurrentUserDep) -> None:
    """타임시트에서 사용 중인 활동유형은 삭제할 수 없다."""
    repo = _get_repo(user.tenant_id)
    document = repo.find_by_id(doc_id)
    if not document:
        raise_not_found(_NOT_FOUND_MESSAGE)

    usage_summary = _collect_usage_summary(
        _get_repo(user.tenant_id, collection=_TIMESHEET_COLLECTION).find_many(
            limit=5000,
            sort=[("created_at", -1)],
        ),
        str(document.get("activity_type", "")).strip(),
    )
    if int(usage_summary.get("timesheet_count", 0) or 0) > 0:
        raise_unprocessable("ERR-PRJ-010", "활동유형이 사용 중이라 삭제할 수 없습니다")
    repo.delete_by_id(doc_id)
