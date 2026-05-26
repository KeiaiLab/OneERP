"""보존 정책(RetentionPolicy) 워크벤치 라우트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_tenant_admin
from oneerp_core.repository import Repository

from ..models.retention_policy import RetentionPolicy, RetentionPolicyCreate, RetentionPolicyUpdate

router = APIRouter(
    prefix="/api/v1/retention-policies",
    tags=["보존 정책"],
    dependencies=[Depends(require_tenant_admin())],
)
_COLLECTION = "retention_policies"
_CATEGORY_COLLECTION = "document_categories"
_DOCUMENT_COLLECTION = "documents"
_PREFIX = "RETP"
_EXPIRY_ALERT_WINDOW_DAYS = 90


def _get_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_category_repo(tenant_id: str) -> Repository:
    return Repository(_CATEGORY_COLLECTION, tenant_id=tenant_id)


def _get_document_repo(tenant_id: str) -> Repository:
    return Repository(_DOCUMENT_COLLECTION, tenant_id=tenant_id)


def _ensure_policy_exists(repo: Repository, policy_id: str) -> dict[str, Any]:
    document = repo.find_by_id(policy_id)
    if not document:
        raise OneERPError(status_code=404, error="not_found", detail="보존 정책을 찾을 수 없습니다")
    return document


def _ensure_unique_policy_name(
    repo: Repository,
    *,
    policy_name: str,
    exclude_id: str | None = None,
) -> None:
    duplicates = repo.find_many({"policy_name": policy_name}, limit=50)
    for duplicate in duplicates:
        if exclude_id and str(duplicate.get("_id") or "") == exclude_id:
            continue
        raise OneERPError(
            status_code=409,
            error="duplicate_policy_name",
            detail="같은 이름의 보존 정책이 이미 존재합니다",
        )


def _retention_period_label(policy: dict[str, Any]) -> str:
    years = int(policy.get("retention_years") or 0)
    months = int(policy.get("retention_months") or 0)
    parts: list[str] = []
    if years:
        parts.append(f"{years}년")
    if months:
        parts.append(f"{months}개월")
    return " ".join(parts) or "0개월"


def _serialize_expiry_date(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC).date().isoformat()
    return None


def _normalize_datetime(value: Any) -> datetime | None:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _policy_categories(category_repo: Repository, policy_id: str) -> list[dict[str, Any]]:
    return category_repo.find_many(
        {"default_retention_policy": policy_id}, limit=1000, sort=[("created_at", -1)]
    )


def _policy_documents(document_repo: Repository, policy_id: str) -> list[dict[str, Any]]:
    return document_repo.find_many(
        {"retention_policy": policy_id, "is_deleted": False},
        limit=2000,
        sort=[("retention_until", 1)],
    )


def _document_summary(policy_documents: list[dict[str, Any]], *, now: datetime) -> dict[str, Any]:
    threshold = now + timedelta(days=_EXPIRY_ALERT_WINDOW_DAYS)
    active_documents = [
        document for document in policy_documents if str(document.get("status") or "") != "disposed"
    ]
    expiring_documents = [
        document
        for document in active_documents
        if (retention_until := _normalize_datetime(document.get("retention_until"))) is not None
        and retention_until <= threshold
    ]
    archived_documents = [
        document for document in policy_documents if str(document.get("status") or "") == "archived"
    ]
    nearest_expiry = None
    if expiring_documents:
        nearest_expiry = min(
            expiry
            for document in expiring_documents
            if (expiry := _normalize_datetime(document.get("retention_until"))) is not None
        )
    return {
        "active_document_count": len(active_documents),
        "archived_document_count": len(archived_documents),
        "expiring_document_count": len(expiring_documents),
        "nearest_expiry_date": _serialize_expiry_date(nearest_expiry),
    }


def _category_summary(policy_categories: list[dict[str, Any]]) -> dict[str, Any]:
    security_levels = sorted(
        {
            str(category.get("default_security_level") or "")
            for category in policy_categories
            if category.get("default_security_level")
        }
    )
    names = [
        str(category.get("name") or category.get("category_name") or "")
        for category in policy_categories
    ]
    return {
        "linked_category_count": len(policy_categories),
        "linked_category_ids": [str(category.get("_id") or "") for category in policy_categories],
        "linked_category_names": names,
        "default_security_levels": security_levels,
    }


def _status_badge_for(
    policy: dict[str, Any], *, category_summary: dict[str, Any], document_summary: dict[str, Any]
) -> str:
    if not policy.get("is_active", True):
        return "inactive"
    if document_summary["expiring_document_count"] > 0 and policy.get("requires_approval", True):
        return "expiry_review_required"
    if document_summary["expiring_document_count"] > 0:
        return "expiry_attention"
    if policy.get("is_system", False):
        return "system_policy"
    if (
        category_summary["linked_category_count"] == 0
        and document_summary["active_document_count"] == 0
    ):
        return "unmapped_policy"
    return "mapped_active"


def _recommended_action_for(
    policy: dict[str, Any],
    *,
    category_summary: dict[str, Any],
    document_summary: dict[str, Any],
) -> str:
    if not policy.get("is_active", True):
        return "activate_policy"
    if document_summary["expiring_document_count"] > 0 and policy.get("requires_approval", True):
        return "review_disposal_queue"
    if document_summary["expiring_document_count"] > 0:
        return "archive_expiring_documents"
    if (
        category_summary["linked_category_count"] == 0
        and document_summary["active_document_count"] == 0
    ):
        return "map_to_categories"
    return "monitor_retention_schedule"


def _available_actions_for(
    policy: dict[str, Any],
    *,
    category_summary: dict[str, Any],
    document_summary: dict[str, Any],
) -> list[str]:
    actions = ["edit", "preview_categories"]
    if document_summary["expiring_document_count"] > 0:
        actions.append("review_expiring_documents")
    if policy.get("is_active", True):
        actions.append("deactivate")
    else:
        actions.append("activate")
    if (
        not policy.get("is_system", False)
        and category_summary["linked_category_count"] == 0
        and document_summary["active_document_count"] == 0
    ):
        actions.append("delete")
    return actions


def _serialize_policy(
    policy: dict[str, Any],
    *,
    category_summary: dict[str, Any],
    document_summary: dict[str, Any],
) -> dict[str, Any]:
    serialized = dict(policy)
    serialized["id"] = str(policy.get("_id") or "")
    serialized["scope_summary"] = {
        "retention_years": int(policy.get("retention_years") or 0),
        "retention_months": int(policy.get("retention_months") or 0),
        "retention_period_label": _retention_period_label(policy),
        "action_on_expiry": str(policy.get("action_on_expiry") or "review"),
        "requires_approval": bool(policy.get("requires_approval", True)),
        "legal_basis": str(policy.get("legal_basis") or ""),
        "linked_category_count": category_summary["linked_category_count"],
        "active_document_count": document_summary["active_document_count"],
        "expiring_document_count": document_summary["expiring_document_count"],
        "nearest_expiry_date": document_summary["nearest_expiry_date"],
    }
    serialized["status_badge"] = _status_badge_for(
        policy,
        category_summary=category_summary,
        document_summary=document_summary,
    )
    serialized["recommended_action"] = _recommended_action_for(
        policy,
        category_summary=category_summary,
        document_summary=document_summary,
    )
    serialized["available_actions"] = _available_actions_for(
        policy,
        category_summary=category_summary,
        document_summary=document_summary,
    )
    serialized["category_summary"] = category_summary
    serialized["document_summary"] = document_summary
    serialized["compliance_summary"] = {
        "action_on_expiry": str(policy.get("action_on_expiry") or "review"),
        "requires_approval": bool(policy.get("requires_approval", True)),
        "legal_basis": str(policy.get("legal_basis") or ""),
        "is_system": bool(policy.get("is_system", False)),
    }
    return serialized


def _matches_filters(
    policy: dict[str, Any],
    *,
    status_badge: str | None,
    action_on_expiry: str | None,
    category_summary: dict[str, Any],
    document_summary: dict[str, Any],
) -> bool:
    if (
        action_on_expiry is not None
        and str(policy.get("action_on_expiry") or "") != action_on_expiry
    ):
        return False
    return (
        status_badge is None
        or _status_badge_for(
            policy,
            category_summary=category_summary,
            document_summary=document_summary,
        )
        == status_badge
    )


def _build_list_summary(serialized_policies: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total_policy_count": len(serialized_policies),
        "active_policy_count": sum(
            1 for policy in serialized_policies if policy.get("is_active", True)
        ),
        "inactive_policy_count": sum(
            1 for policy in serialized_policies if not policy.get("is_active", True)
        ),
        "system_policy_count": sum(
            1 for policy in serialized_policies if policy.get("is_system", False)
        ),
        "approval_required_count": sum(
            1 for policy in serialized_policies if policy.get("requires_approval", True)
        ),
        "mapped_category_count": sum(
            policy["category_summary"]["linked_category_count"] for policy in serialized_policies
        ),
        "expiring_document_count": sum(
            policy["document_summary"]["expiring_document_count"] for policy in serialized_policies
        ),
    }


def _prepare_payload(body: dict[str, Any]) -> dict[str, Any]:
    payload = dict(body)
    payload["policy_name"] = str(payload.get("policy_name") or "").strip()
    payload["description"] = str(payload.get("description") or "").strip()
    payload["legal_basis"] = str(payload.get("legal_basis") or "").strip()
    return payload


def _ensure_deletable(
    policy: dict[str, Any],
    *,
    category_summary: dict[str, Any],
    document_summary: dict[str, Any],
) -> None:
    if policy.get("is_system", False):
        raise OneERPError(
            status_code=422,
            error="ERR-DOC-201",
            detail="시스템 기본 보존 정책은 삭제할 수 없습니다",
        )
    if (
        category_summary["linked_category_count"] > 0
        or document_summary["active_document_count"] > 0
    ):
        raise OneERPError(
            status_code=422,
            error="ERR-DOC-202",
            detail="연결된 문서 분류 또는 문서가 있는 보존 정책은 삭제할 수 없습니다",
        )


@router.post("", status_code=201)
async def create_retention_policy(
    body: RetentionPolicyCreate, user: CurrentUserDep
) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    payload = _prepare_payload(body.model_dump())
    _ensure_unique_policy_name(repo, policy_name=payload["policy_name"])
    policy_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    document = RetentionPolicy(_id=policy_id, **payload)
    repo.insert(document)
    return {
        "retention_policy_id": policy_id,
        "id": policy_id,
        "message": "보존 정책이 생성되었습니다",
    }


@router.get("")
async def list_retention_policies(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    status_badge: str | None = None,
    action_on_expiry: str | None = None,
) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    category_repo = _get_category_repo(user.tenant_id)
    document_repo = _get_document_repo(user.tenant_id)
    policies = repo.find_many({}, limit=1000, sort=[("created_at", -1)])
    now = datetime.now(UTC)

    serialized_policies: list[dict[str, Any]] = []
    for policy in policies:
        category_summary = _category_summary(
            _policy_categories(category_repo, str(policy.get("_id") or ""))
        )
        document_summary = _document_summary(
            _policy_documents(document_repo, str(policy.get("_id") or "")),
            now=now,
        )
        if not _matches_filters(
            policy,
            status_badge=status_badge,
            action_on_expiry=action_on_expiry,
            category_summary=category_summary,
            document_summary=document_summary,
        ):
            continue
        serialized_policies.append(
            _serialize_policy(
                policy,
                category_summary=category_summary,
                document_summary=document_summary,
            )
        )

    total = len(serialized_policies)
    start = max(page - 1, 0) * page_size
    end = start + page_size
    return {
        "data": serialized_policies[start:end],
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": _build_list_summary(serialized_policies),
    }


@router.get("/{policy_id}")
async def get_retention_policy(policy_id: str, user: CurrentUserDep) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    category_repo = _get_category_repo(user.tenant_id)
    document_repo = _get_document_repo(user.tenant_id)
    policy = _ensure_policy_exists(repo, policy_id)
    return _serialize_policy(
        policy,
        category_summary=_category_summary(_policy_categories(category_repo, policy_id)),
        document_summary=_document_summary(
            _policy_documents(document_repo, policy_id), now=datetime.now(UTC)
        ),
    )


@router.get("/{policy_id}/summary")
async def get_retention_policy_summary(policy_id: str, user: CurrentUserDep) -> dict[str, Any]:
    return await get_retention_policy(policy_id, user)


@router.put("/{policy_id}")
async def update_retention_policy(
    policy_id: str,
    body: RetentionPolicyUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    repo = _get_repo(user.tenant_id)
    policy = _ensure_policy_exists(repo, policy_id)
    payload = {
        key: value
        for key, value in _prepare_payload(body.model_dump(exclude_unset=True)).items()
        if value is not None
    }
    if "policy_name" in payload:
        _ensure_unique_policy_name(repo, policy_name=payload["policy_name"], exclude_id=policy_id)
    repo.update_by_id(policy_id, {**payload, "updated_by": user.sub})
    updated = {**policy, **payload}
    category_repo = _get_category_repo(user.tenant_id)
    document_repo = _get_document_repo(user.tenant_id)
    return _serialize_policy(
        updated,
        category_summary=_category_summary(_policy_categories(category_repo, policy_id)),
        document_summary=_document_summary(
            _policy_documents(document_repo, policy_id), now=datetime.now(UTC)
        ),
    )


@router.delete("/{policy_id}", status_code=204)
async def delete_retention_policy(policy_id: str, user: CurrentUserDep) -> None:
    repo = _get_repo(user.tenant_id)
    category_repo = _get_category_repo(user.tenant_id)
    document_repo = _get_document_repo(user.tenant_id)
    policy = _ensure_policy_exists(repo, policy_id)
    category_summary = _category_summary(_policy_categories(category_repo, policy_id))
    document_summary = _document_summary(
        _policy_documents(document_repo, policy_id), now=datetime.now(UTC)
    )
    _ensure_deletable(policy, category_summary=category_summary, document_summary=document_summary)
    repo.delete_by_id(policy_id)
