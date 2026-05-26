"""위임규칙(DelegationRule) 관리 라우트."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.delegation_rule import (
    DelegationRule,
    DelegationRuleCreate,
    DelegationRuleUpdate,
)

router = APIRouter(prefix="/api/v1/delegation-rules", tags=["위임규칙"])
_COLLECTION = "delegation_rules"
_PREFIX = "DR"
_EXPIRING_SOON_DAYS = 3


def _get_repo(tenant_id: str = "") -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _normalize_rule_date(value: date | datetime | None) -> date | None:
    """저장된 날짜/일시 값을 date로 정규화한다."""
    if isinstance(value, datetime):
        return value.date()
    return value


def _matches_document_type(rule_document_type: str, target_document_type: str) -> bool:
    """문서유형 필터링 규칙을 판정한다."""
    normalized_rule = (rule_document_type or "").strip()
    normalized_target = (target_document_type or "").strip()
    if not normalized_target:
        return True
    return not normalized_rule or normalized_rule == normalized_target


def _resolve_rule_status(rule: dict[str, Any], as_of: date) -> str:
    """위임 규칙의 실효 상태를 계산한다."""
    from_date = _normalize_rule_date(rule.get("from_date"))
    to_date = _normalize_rule_date(rule.get("to_date"))
    if not rule.get("is_active", True):
        return "inactive"
    if to_date and to_date < as_of:
        return "expired"
    if from_date and from_date > as_of:
        return "inactive"
    return "active"


def _get_remaining_days(rule: dict[str, Any], as_of: date) -> int | None:
    to_date = _normalize_rule_date(rule.get("to_date"))
    if not to_date:
        return None
    return (to_date - as_of).days


def _is_expiring_soon(rule: dict[str, Any], as_of: date) -> bool:
    if _resolve_rule_status(rule, as_of) != "active":
        return False
    remaining_days = _get_remaining_days(rule, as_of)
    return remaining_days is not None and 0 <= remaining_days <= _EXPIRING_SOON_DAYS


def _build_scope_summary(rule: dict[str, Any], as_of: date) -> dict[str, Any]:
    document_type = (rule.get("document_type") or "").strip()
    return {
        "rule_scope": "all_documents" if not document_type else "document_scoped",
        "document_type": document_type,
        "applies_to_all_documents": not document_type,
        "remaining_days": _get_remaining_days(rule, as_of),
        "is_expiring_soon": _is_expiring_soon(rule, as_of),
    }


def _build_available_actions(rule_status: str) -> list[str]:
    if rule_status == "active":
        return ["edit", "deactivate", "delete"]
    return ["edit", "activate", "delete"]


def _get_status_badge(rule: dict[str, Any], as_of: date) -> str:
    rule_status = _resolve_rule_status(rule, as_of)
    if rule_status == "expired":
        return "expired"
    if rule_status == "inactive":
        return "inactive"
    if _is_expiring_soon(rule, as_of):
        return "expiring_soon"
    return "active_global" if not (rule.get("document_type") or "").strip() else "active_scoped"


def _get_recommended_action(rule: dict[str, Any], as_of: date) -> str:
    rule_status = _resolve_rule_status(rule, as_of)
    if rule_status == "expired":
        return "renew_rule"
    if rule_status == "inactive":
        return "activate_rule"
    if _is_expiring_soon(rule, as_of):
        return "extend_rule"
    if not (rule.get("document_type") or "").strip():
        return "monitor_rule_usage"
    return "check_document_scope"


def _serialize_rule(rule: dict[str, Any], *, as_of: date) -> dict[str, Any]:
    """API 응답에 필요한 위임 규칙 파생 필드를 추가한다."""
    rule_status = _resolve_rule_status(rule, as_of)
    scope_summary = _build_scope_summary(rule, as_of)
    return {
        **rule,
        "_id": str(rule.get("_id", "")),
        "rule_status": rule_status,
        "applies_to_all_documents": scope_summary["applies_to_all_documents"],
        "status_badge": _get_status_badge(rule, as_of),
        "scope_summary": scope_summary,
        "recommended_action": _get_recommended_action(rule, as_of),
        "available_actions": _build_available_actions(rule_status),
    }


def _validate_date_range(from_date: date | None, to_date: date | None) -> None:
    """시작일/종료일 역전 여부를 검증한다."""
    if from_date and to_date and from_date > to_date:
        raise OneERPError(
            status_code=422,
            error="invalid_date_range",
            detail="위임 종료일은 시작일보다 빠를 수 없습니다",
        )


def _date_ranges_overlap(
    left_from: date | None,
    left_to: date | None,
    right_from: date | None,
    right_to: date | None,
) -> bool:
    start_left = left_from or date.min
    end_left = left_to or date.max
    start_right = right_from or date.min
    end_right = right_to or date.max
    return start_left <= end_right and start_right <= end_left


def _document_scope_overlaps(left_document_type: str, right_document_type: str) -> bool:
    left = (left_document_type or "").strip()
    right = (right_document_type or "").strip()
    return not left or not right or left == right


def _validate_overlap(
    repo: Repository,
    *,
    delegator: str,
    document_type: str,
    from_date: date | None,
    to_date: date | None,
    is_active: bool,
    exclude_id: str | None = None,
) -> None:
    """같은 위임자/범위에 겹치는 활성 규칙이 있는지 확인한다."""
    if not is_active:
        return

    candidates = repo.find_many({"delegator": delegator}, limit=1000, sort=[("created_at", -1)])
    for rule in candidates:
        if exclude_id and str(rule.get("_id", "")) == exclude_id:
            continue
        if not rule.get("is_active", True):
            continue
        if not _document_scope_overlaps(rule.get("document_type", ""), document_type):
            continue
        if _date_ranges_overlap(
            _normalize_rule_date(rule.get("from_date")),
            _normalize_rule_date(rule.get("to_date")),
            from_date,
            to_date,
        ):
            raise OneERPError(
                status_code=422,
                error="ERR-APR-012",
                detail="같은 위임자에 대해 기간이 겹치는 활성 위임 규칙은 등록할 수 없습니다",
            )


def _build_summary(serialized_rules: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "active": 0,
        "inactive": 0,
        "expired": 0,
        "global_scope_count": 0,
        "scoped_rule_count": 0,
        "expiring_soon_count": 0,
    }
    for rule in serialized_rules:
        summary[rule["rule_status"]] += 1
        if rule["scope_summary"]["applies_to_all_documents"]:
            summary["global_scope_count"] += 1
        else:
            summary["scoped_rule_count"] += 1
        if rule["scope_summary"]["is_expiring_soon"]:
            summary["expiring_soon_count"] += 1
    return summary


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("delegation_rule:create"))]
)
async def create_delegation_rule(body: DelegationRuleCreate, user: CurrentUserDep) -> dict:
    """위임규칙을 생성한다."""
    repo = _get_repo(user.tenant_id)
    _validate_date_range(body.from_date, body.to_date)
    _validate_overlap(
        repo,
        delegator=body.delegator,
        document_type=body.document_type,
        from_date=body.from_date,
        to_date=body.to_date,
        is_active=body.is_active,
    )
    doc_id = generate_name(_PREFIX)
    doc = DelegationRule(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"delegation_rule_id": doc_id, "message": "위임규칙이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("delegation_rule:read"))])
async def list_delegation_rules(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    delegator: str | None = None,
    delegate: str | None = None,
    document_type: str | None = None,
    status: str | None = None,
    as_of_date: date | None = None,
) -> dict:
    """위임규칙 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if delegator:
        query["delegator"] = delegator
    if delegate:
        query["delegate"] = delegate

    as_of = as_of_date or datetime.now(UTC).date()
    all_rules = repo.find_many(query=query, limit=1000, sort=[("created_at", -1)])
    serialized_rules = []
    for rule in all_rules:
        if document_type and not _matches_document_type(
            rule.get("document_type", ""), document_type
        ):
            continue
        serialized = _serialize_rule(rule, as_of=as_of)
        if status and serialized["rule_status"] != status:
            continue
        serialized_rules.append(serialized)

    summary = _build_summary(serialized_rules)
    skip = (page - 1) * page_size
    return {
        "data": serialized_rules[skip : skip + page_size],
        "total": len(serialized_rules),
        "page": page,
        "page_size": page_size,
        "summary": summary,
        "as_of_date": as_of,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("delegation_rule:read"))])
async def get_delegation_rule(
    doc_id: str,
    user: CurrentUserDep,
    as_of_date: date | None = None,
) -> dict:
    """위임규칙 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="위임규칙을 찾을 수 없습니다")
    return _serialize_rule(doc, as_of=as_of_date or datetime.now(UTC).date())


@router.put("/{doc_id}", dependencies=[Depends(require_permission("delegation_rule:write"))])
async def update_delegation_rule(
    doc_id: str, body: DelegationRuleUpdate, user: CurrentUserDep
) -> dict:
    """위임규칙을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="위임규칙을 찾을 수 없습니다")

    merged = {**doc, **body.model_dump(exclude_none=True)}
    from_date = _normalize_rule_date(merged.get("from_date"))
    to_date = _normalize_rule_date(merged.get("to_date"))
    _validate_date_range(from_date, to_date)
    _validate_overlap(
        repo,
        delegator=str(merged.get("delegator", "")),
        document_type=str(merged.get("document_type", "")),
        from_date=from_date,
        to_date=to_date,
        is_active=bool(merged.get("is_active", True)),
        exclude_id=doc_id,
    )
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "위임규칙이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("delegation_rule:delete"))])
async def delete_delegation_rule(doc_id: str, user: CurrentUserDep) -> dict:
    """위임규칙을 삭제한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="위임규칙을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "위임규칙이 삭제되었습니다"}
