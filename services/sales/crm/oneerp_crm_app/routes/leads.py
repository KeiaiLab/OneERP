"""리드(Lead) API 라우터."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_conflict, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_crm_app.models.lead import Lead, LeadCreate, LeadUpdate
from oneerp_crm_app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/api/v1/leads", tags=["리드"])

_COLLECTION = "leads"
_PREFIX = "LEAD"
_LEAD_ACTIVITY_COLLECTION = "activities"
_LEAD_OPPORTUNITY_COLLECTION = "opportunities"
_STALE_ACTIVITY_DAYS = 7


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_activity_repo(_tenant_id: str) -> Repository:
    """리드 활동 조회용 Repository를 반환한다."""
    return Repository(_LEAD_ACTIVITY_COLLECTION)


def _get_opportunity_repo(tenant_id: str) -> Repository:
    """리드 연계 기회 조회용 Repository를 반환한다."""
    return Repository(_LEAD_OPPORTUNITY_COLLECTION, tenant_id=tenant_id)


def _normalize_email(email: str) -> str:
    """중복 비교를 위해 이메일을 정규화한다."""
    return email.strip().lower()


def _coerce_datetime(value: Any) -> datetime | None:
    """문서 날짜/문자열을 UTC datetime으로 변환한다."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)
    return None


def _serialize_date(value: Any) -> str:
    """날짜 값을 ISO 문자열로 직렬화한다."""
    parsed = _coerce_datetime(value)
    if parsed is not None:
        return parsed.date().isoformat()
    return str(value or "")


def _score_grade(score: Any) -> str:
    """리드 점수를 운영 배지용 등급으로 정규화한다."""
    numeric = float(score or 0)
    if numeric >= 80:
        return "hot"
    if numeric >= 50:
        return "warm"
    if numeric >= 20:
        return "cool"
    return "cold"


def _lead_activity_summary(activity_docs: list[dict[str, Any]]) -> dict[str, Any]:
    """리드 활동 요약을 계산한다."""
    if not activity_docs:
        return {
            "activity_count": 0,
            "latest_activity_type": "",
            "latest_activity_date": "",
            "assigned_owner_count": 0,
            "activity_mix": {},
        }

    latest_doc = max(
        activity_docs,
        key=lambda doc: (
            _coerce_datetime(doc.get("activity_date") or doc.get("created_at"))
            or datetime.min.replace(tzinfo=UTC)
        ),
    )
    activity_mix = Counter(str(doc.get("activity_type", "")) for doc in activity_docs if doc)
    assigned_owner_count = len(
        {str(doc.get("assigned_to", "")).strip() for doc in activity_docs if doc.get("assigned_to")}
    )
    return {
        "activity_count": len(activity_docs),
        "latest_activity_type": str(latest_doc.get("activity_type", "")),
        "latest_activity_date": _serialize_date(
            latest_doc.get("activity_date") or latest_doc.get("created_at")
        ),
        "assigned_owner_count": assigned_owner_count,
        "activity_mix": dict(activity_mix),
    }


def _lead_conversion_summary(
    lead: dict[str, Any], opportunities: list[dict[str, Any]]
) -> dict[str, Any]:
    """리드 전환 컨텍스트를 계산한다."""
    linked_opportunity_ids = [str(doc.get("_id", "")) for doc in opportunities]
    status = str(lead.get("status", "open")).lower()
    return {
        "status": status,
        "can_convert_to_opportunity": status == "qualified",
        "linked_opportunity_count": len(linked_opportunity_ids),
        "linked_opportunity_ids": linked_opportunity_ids,
    }


def _lead_status_badge(
    lead: dict[str, Any],
    score_grade: str,
    activity_summary: dict[str, Any],
    conversion_summary: dict[str, Any],
) -> str:
    """리드 상태 배지를 결정한다."""
    status = str(lead.get("status", "open")).lower()
    if status == "converted":
        return "converted_pipeline"
    if status == "qualified" and score_grade == "hot":
        return "qualified_hot"
    if status == "qualified":
        return "qualified_ready"
    if conversion_summary["linked_opportunity_count"] > 0:
        return "converted_pipeline"
    if status == "contacted" and activity_summary["activity_count"] > 0:
        return "contacted_active"
    if status == "lost":
        return "lost_reengage"
    if score_grade in {"hot", "warm"}:
        return "engaged_open"
    return "new_lead"


def _lead_recommended_action(
    lead: dict[str, Any],
    activity_summary: dict[str, Any],
    conversion_summary: dict[str, Any],
) -> str:
    """리드의 다음 권장 액션을 계산한다."""
    status = str(lead.get("status", "open")).lower()
    if status == "qualified":
        return "convert_to_opportunity"
    if status == "converted" or conversion_summary["linked_opportunity_count"] > 0:
        return "review_opportunity_pipeline"
    if status == "lost":
        return "reengage_lead"
    if activity_summary["activity_count"] == 0:
        return "record_first_activity"
    return "qualify_lead"


def _lead_available_actions(
    lead: dict[str, Any],
    conversion_summary: dict[str, Any],
) -> list[str]:
    """리드 상세/목록에서 노출할 액션 목록을 계산한다."""
    status = str(lead.get("status", "open")).lower()
    actions = ["edit", "log_activity"]
    if status == "qualified":
        actions.append("convert_to_opportunity")
    elif status == "lost":
        actions.append("reopen_lead")
    elif conversion_summary["linked_opportunity_count"] > 0:
        actions.append("open_opportunities")
    else:
        actions.append("qualify_lead")
    if status != "converted" and conversion_summary["linked_opportunity_count"] == 0:
        actions.append("delete")
    return actions


def _decorate_lead(
    lead: dict[str, Any],
    all_activities: list[dict[str, Any]],
    all_opportunities: list[dict[str, Any]],
) -> dict[str, Any]:
    """리드 문서를 워크벤치 응답으로 확장한다."""
    lead_id = str(lead.get("_id", ""))
    lead_activities = [
        doc
        for doc in all_activities
        if str(doc.get("lead_id", "")) == lead_id
        or (
            str(doc.get("party_type", "")).lower() == "lead"
            and str(doc.get("party", "")) == lead_id
        )
    ]
    related_opportunities = [
        doc for doc in all_opportunities if str(doc.get("lead_ref", "")) == lead_id
    ]
    score = float(lead.get("lead_score", 0) or 0)
    score_grade = _score_grade(score)
    activity_summary = _lead_activity_summary(lead_activities)
    conversion_summary = _lead_conversion_summary(lead, related_opportunities)
    status_badge = _lead_status_badge(
        lead,
        score_grade=score_grade,
        activity_summary=activity_summary,
        conversion_summary=conversion_summary,
    )
    recommended_action = _lead_recommended_action(
        lead,
        activity_summary=activity_summary,
        conversion_summary=conversion_summary,
    )
    available_actions = _lead_available_actions(
        lead,
        conversion_summary=conversion_summary,
    )
    return {
        **lead,
        "score_summary": {
            "lead_score": score,
            "score_grade": score_grade,
        },
        "activity_summary": activity_summary,
        "conversion_summary": conversion_summary,
        "status_badge": status_badge,
        "recommended_action": recommended_action,
        "available_actions": available_actions,
    }


def _build_listing_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """리드 목록 상단 요약을 계산한다."""
    status_counter = Counter(str(row.get("status", "open")).lower() for row in rows)
    stale_threshold = datetime.now(UTC) - timedelta(days=_STALE_ACTIVITY_DAYS)
    stale_follow_up_count = 0
    for row in rows:
        status = str(row.get("status", "open")).lower()
        if status in {"converted", "lost"}:
            continue
        latest = _coerce_datetime(row["activity_summary"]["latest_activity_date"])
        if latest is None or latest < stale_threshold:
            stale_follow_up_count += 1
    return {
        "total_count": len(rows),
        "open_count": status_counter["open"],
        "contacted_count": status_counter["contacted"],
        "qualified_count": status_counter["qualified"],
        "converted_count": status_counter["converted"],
        "lost_count": status_counter["lost"],
        "high_score_count": sum(1 for row in rows if row["score_summary"]["score_grade"] == "hot"),
        "conversion_ready_count": sum(
            1 for row in rows if row["conversion_summary"]["can_convert_to_opportunity"]
        ),
        "with_activity_count": sum(
            1 for row in rows if row["activity_summary"]["activity_count"] > 0
        ),
        "stale_follow_up_count": stale_follow_up_count,
    }


def _matches_filters(
    lead: dict[str, Any],
    *,
    status: str,
    source: str,
    score_grade: str,
    q: str,
) -> bool:
    """리드 목록 검색/필터를 적용한다."""
    normalized_status = status.strip().lower()
    if normalized_status and str(lead.get("status", "")).lower() != normalized_status:
        return False
    normalized_source = source.strip().lower()
    if normalized_source and str(lead.get("source", "")).lower() != normalized_source:
        return False
    normalized_grade = score_grade.strip().lower()
    if normalized_grade and _score_grade(lead.get("lead_score", 0)) != normalized_grade:
        return False
    normalized_q = q.strip().lower()
    if normalized_q:
        haystack = " ".join(
            [
                str(lead.get("lead_name", "")),
                str(lead.get("company_name", "")),
                str(lead.get("email", "")),
                str(lead.get("interested_item", "")),
            ]
        ).lower()
        if normalized_q not in haystack:
            return False
    return True


def _ensure_unique_email(
    repo: Repository, email: str, *, current_doc_id: str | None = None
) -> None:
    """동일 이메일 리드 중복 생성을 막는다."""
    normalized = _normalize_email(email)
    if not normalized:
        return
    existing_docs = repo.find_many(limit=5000)
    for existing in existing_docs:
        if str(existing.get("_id", "")) == current_doc_id:
            continue
        if _normalize_email(str(existing.get("email", ""))) == normalized:
            raise_conflict("이미 등록된 리드 이메일입니다")


@router.post("", status_code=201, dependencies=[Depends(require_permission("lead:create"))])
def create_lead(body: LeadCreate, user: CurrentUserDep) -> dict[str, Any]:
    """리드를 생성한다."""
    repo = _get_repo(user.tenant_id)
    _ensure_unique_email(repo, body.email)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    lead = Lead(
        _id=doc_id,
        tenant_id=user.tenant_id,
        lead_name=body.lead_name,
        company_name=body.company_name,
        email=_normalize_email(body.email),
        phone=body.phone,
        source=body.source,
        interested_item=body.interested_item,
        assigned_to=body.assigned_to,
        lead_score=body.lead_score,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(lead)
    return {"id": doc_id, "message": "리드가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("lead:read"))])
def list_leads(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    status: str = "",
    source: str = "",
    score_grade: str = "",
    q: str = "",
) -> dict[str, Any]:
    """리드 목록을 워크벤치 요약과 함께 조회한다."""
    repo = _get_repo(user.tenant_id)
    activity_repo = _get_activity_repo(user.tenant_id)
    opportunity_repo = _get_opportunity_repo(user.tenant_id)

    all_docs = repo.find_many(limit=5000, sort=[("created_at", -1)])
    all_activities = activity_repo.find_many(limit=5000, sort=[("activity_date", -1)])
    all_opportunities = opportunity_repo.find_many(limit=5000, sort=[("created_at", -1)])

    filtered_docs = [
        doc
        for doc in all_docs
        if _matches_filters(doc, status=status, source=source, score_grade=score_grade, q=q)
    ]
    decorated_docs = [
        _decorate_lead(doc, all_activities=all_activities, all_opportunities=all_opportunities)
        for doc in filtered_docs
    ]
    skip = max(page - 1, 0) * page_size
    paged_docs = decorated_docs[skip : skip + page_size]
    return {
        "data": paged_docs,
        "summary": _build_listing_summary(decorated_docs),
        "total": len(decorated_docs),
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("lead:read"))])
def get_lead(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """리드 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("리드를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    activity_repo = _get_activity_repo(user.tenant_id)
    opportunity_repo = _get_opportunity_repo(user.tenant_id)
    return _decorate_lead(
        doc,
        all_activities=activity_repo.find_many(limit=5000, sort=[("activity_date", -1)]),
        all_opportunities=opportunity_repo.find_many(limit=5000, sort=[("created_at", -1)]),
    )


@router.get("/{doc_id}/summary", dependencies=[Depends(require_permission("lead:read"))])
def get_lead_summary(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """리드 활동/점수/전환 준비 요약을 조회한다."""
    return get_lead(doc_id, user)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("lead:write"))])
def update_lead(
    doc_id: str,
    body: LeadUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """리드를 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("리드를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    if "email" in update_data:
        _ensure_unique_email(repo, str(update_data["email"]), current_doc_id=doc_id)
        update_data["email"] = _normalize_email(str(update_data["email"]))
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "리드가 수정되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("lead:delete"))]
)
def delete_lead(doc_id: str, user: CurrentUserDep) -> None:
    """리드를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("리드를 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    repo.delete_by_id(doc_id)


@router.post(
    "/{doc_id}/convert",
    dependencies=[Depends(require_permission("lead:write"))],
)
def convert_lead(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """리드를 기회로 전환한다."""
    service = PipelineService(tenant_id=user.tenant_id)
    try:
        return service.convert_lead_to_opportunity(doc_id)
    except ValueError as e:
        raise_bad_request(str(e))
