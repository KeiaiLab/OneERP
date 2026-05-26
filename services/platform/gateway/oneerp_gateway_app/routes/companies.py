"""회사(Company) CRUD 라우터."""

from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.company import Company, CompanyCreate, CompanyUpdate

router = APIRouter(prefix="/api/v1/companies", tags=["회사"])

_COLLECTION = "companies"
_PREFIX = "COMP"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _normalize_company_code(raw_code: str) -> str:
    """회사 코드를 저장용 포맷으로 정규화한다."""
    normalized = re.sub(r"[^A-Z0-9-]", "-", raw_code.upper())
    return re.sub(r"-{2,}", "-", normalized).strip("-")


def _find_duplicate(
    repo: Repository,
    field_name: str,
    value: str,
    *,
    current_id: str | None = None,
) -> dict[str, Any] | None:
    """동일 테넌트 내 중복 회사를 찾는다."""
    if not value:
        return None
    for match in repo.find_many(query={field_name: value}, limit=20):
        if match.get("_id") != current_id:
            return match
    return None


def _validate_parent_company(
    repo: Repository, parent_company_id: str, doc_id: str | None = None
) -> None:
    """상위 회사를 검증한다."""
    if not parent_company_id:
        return
    if doc_id and parent_company_id == doc_id:
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="회사를 자기 자신의 상위 회사로 설정할 수 없습니다",
        )
    if not repo.find_by_id(parent_company_id):
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="상위 회사를 찾을 수 없습니다",
        )


def _validate_unique_fields(
    repo: Repository,
    *,
    company_name: str,
    abbr: str,
    company_code: str,
    business_registration_number: str,
    current_id: str | None = None,
) -> None:
    """회사 프로필의 유니크 필드를 검증한다."""
    for field_name, value, detail in (
        ("company_name", company_name, "같은 회사명은 같은 테넌트에서 중복 저장할 수 없습니다"),
        ("abbr", abbr, "같은 약칭은 같은 테넌트에서 중복 저장할 수 없습니다"),
        ("company_code", company_code, "같은 회사 코드는 같은 테넌트에서 중복 저장할 수 없습니다"),
        (
            "business_registration_number",
            business_registration_number,
            "같은 사업자등록번호는 같은 테넌트에서 중복 저장할 수 없습니다",
        ),
    ):
        duplicate = _find_duplicate(repo, field_name, value, current_id=current_id)
        if duplicate:
            raise OneERPError(status_code=422, error="validation_error", detail=detail)


def _clear_existing_default_companies(
    repo: Repository, *, user_sub: str, exclude_id: str | None = None
) -> None:
    """현재 기본 회사 플래그를 해제한다."""
    for company in repo.find_many(query={"is_default": True}, limit=200):
        if company.get("_id") == exclude_id:
            continue
        repo.update_by_id(company["_id"], {"is_default": False, "updated_by": user_sub})


def _build_child_map(companies: list[dict[str, Any]]) -> dict[str, list[str]]:
    child_map: dict[str, list[str]] = {company["_id"]: [] for company in companies}
    for company in companies:
        parent_company_id = company.get("parent_company_id") or ""
        if parent_company_id:
            child_map.setdefault(parent_company_id, []).append(company["_id"])
    return child_map


def _status_badge_for(company: dict[str, Any], child_map: dict[str, list[str]]) -> str:
    if not company.get("is_active", True):
        return "inactive"
    if company.get("is_default"):
        return "default_company"
    if child_map.get(company["_id"]):
        return "group_company"
    if company.get("parent_company_id"):
        return "branch_company"
    return "active_company"


def _recommended_action_for(company: dict[str, Any], child_map: dict[str, list[str]]) -> str:
    child_company_count = len(child_map.get(company["_id"], []))
    if not company.get("is_active", True):
        return "reactivate_company"
    if company.get("is_default") and child_company_count == 0:
        return "create_branch_company"
    if company.get("is_default"):
        return "review_company_tree"
    if company.get("parent_company_id"):
        return "review_company_switcher"
    return "set_default_company"


def _available_actions_for(company: dict[str, Any], child_map: dict[str, list[str]]) -> list[str]:
    actions = ["edit", "open_company_tree", "manage_currency"]
    if company.get("is_active", True):
        actions.append("deactivate")
    else:
        actions.append("reactivate")
    if not company.get("is_default"):
        actions.append("set_default_company")
    if not child_map.get(company["_id"]):
        actions.append("delete")
    if not company.get("parent_company_id"):
        actions.append("create_branch_company")
    return actions


def _decorate_company(company: dict[str, Any], child_map: dict[str, list[str]]) -> dict[str, Any]:
    child_company_ids = child_map.get(company["_id"], [])
    return {
        **company,
        "status_badge": _status_badge_for(company, child_map),
        "recommended_action": _recommended_action_for(company, child_map),
        "available_actions": _available_actions_for(company, child_map),
        "hierarchy_summary": {
            "is_default": company.get("is_default", False),
            "is_active": company.get("is_active", True),
            "is_root": not bool(company.get("parent_company_id")),
            "parent_company_id": company.get("parent_company_id", ""),
            "child_company_count": len(child_company_ids),
            "child_company_ids": child_company_ids,
            "default_currency": company.get("default_currency", "KRW"),
        },
    }


def _build_company_tree(
    companies: list[dict[str, Any]], child_map: dict[str, list[str]]
) -> list[dict[str, Any]]:
    """회사 목록을 트리 구조로 변환한다."""
    nodes = []
    node_map: dict[str, dict[str, Any]] = {}
    for company in companies:
        node = {**_decorate_company(company, child_map), "children": []}
        node_map[company["_id"]] = node
        nodes.append(node)

    roots: list[dict[str, Any]] = []
    for node in nodes:
        parent_id = node.get("parent_company_id") or ""
        parent = node_map.get(parent_id)
        if parent is None:
            roots.append(node)
            continue
        parent["children"].append(node)
    return roots


def _build_company_summary(companies: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "total_company_count": len(companies),
        "active_company_count": sum(1 for company in companies if company.get("is_active", True)),
        "inactive_company_count": sum(
            1 for company in companies if not company.get("is_active", True)
        ),
        "default_company_count": sum(1 for company in companies if company.get("is_default")),
        "root_company_count": sum(
            1 for company in companies if not company.get("parent_company_id")
        ),
        "branch_company_count": sum(1 for company in companies if company.get("parent_company_id")),
    }


def _matches_list_filters(
    company: dict[str, Any],
    *,
    active_only: bool,
    parent_company_id: str | None,
    is_default: bool | None,
    status_badge: str | None,
) -> bool:
    if active_only and not company.get("is_active", True):
        return False
    if (
        parent_company_id is not None
        and (company.get("parent_company_id") or "") != parent_company_id
    ):
        return False
    if is_default is not None and bool(company.get("is_default")) != is_default:
        return False
    return not (status_badge and company.get("status_badge") != status_badge)


@router.post("", status_code=201, dependencies=[Depends(require_permission("company:create"))])
async def create_company(body: CompanyCreate, user: CurrentUserDep) -> dict[str, Any]:
    """회사를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    company_code = _normalize_company_code(body.company_code or body.abbr)

    _validate_parent_company(repo, body.parent_company_id)
    _validate_unique_fields(
        repo,
        company_name=body.company_name,
        abbr=body.abbr,
        company_code=company_code,
        business_registration_number=body.business_registration_number,
    )

    existing_defaults = repo.find_many(query={"is_default": True}, limit=1)
    is_default = body.is_default or not existing_defaults
    if is_default:
        _clear_existing_default_companies(repo, user_sub=user.sub)

    company = Company(
        _id=doc_id,
        tenant_id=user.tenant_id,
        company_name=body.company_name,
        abbr=body.abbr,
        company_code=company_code,
        business_registration_number=body.business_registration_number,
        representative_name=body.representative_name,
        address=body.address,
        default_currency=body.default_currency,
        country=body.country,
        chart_of_accounts=body.chart_of_accounts,
        fiscal_year_start=body.fiscal_year_start,
        domain=body.domain,
        parent_company_id=body.parent_company_id,
        is_default=is_default,
        is_active=body.is_active,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(company)
    return {"id": doc_id, "message": "회사가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("company:read"))])
async def list_companies(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    *,
    active_only: bool = False,
    parent_company_id: str | None = None,
    is_default: bool | None = None,
    status_badge: str | None = None,
) -> dict[str, Any]:
    """회사 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    companies = repo.find_many(
        limit=500, sort=[("is_default", -1), ("company_code", 1), ("created_at", -1)]
    )
    child_map = _build_child_map(companies)
    enriched = [_decorate_company(company, child_map) for company in companies]
    filtered = [
        company
        for company in enriched
        if _matches_list_filters(
            company,
            active_only=active_only,
            parent_company_id=parent_company_id,
            is_default=is_default,
            status_badge=status_badge,
        )
    ]
    skip = (page - 1) * page_size
    return {
        "data": filtered[skip : skip + page_size],
        "total": len(filtered),
        "page": page,
        "page_size": page_size,
        "summary": _build_company_summary(filtered),
    }


@router.get("/tree", dependencies=[Depends(require_permission("company:read"))])
async def get_company_tree(user: CurrentUserDep) -> dict[str, Any]:
    """회사를 상하위 법인 트리로 조회한다."""
    repo = _get_repo(user.tenant_id)
    companies = repo.find_many(limit=500, sort=[("company_code", 1), ("created_at", 1)])
    child_map = _build_child_map(companies)
    roots = _build_company_tree(companies, child_map)
    default_company_id = next(
        (company["_id"] for company in companies if company.get("is_default")),
        "",
    )
    return {
        "data": roots,
        "total": len(companies),
        "default_company_id": default_company_id,
        "summary": _build_company_summary(companies),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("company:read"))])
async def get_company(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """회사 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="회사를 찾을 수 없습니다")
    companies = repo.find_many(limit=500, sort=[("company_code", 1), ("created_at", 1)])
    child_map = _build_child_map(companies)
    return _decorate_company(doc, child_map)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("company:write"))])
async def update_company(
    doc_id: str,
    body: CompanyUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """회사를 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="회사를 찾을 수 없습니다")

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="bad_request", detail="수정할 내용이 없습니다")

    merged = {**doc, **update_data}
    company_code = _normalize_company_code(merged.get("company_code") or merged.get("abbr") or "")
    update_data["company_code"] = company_code

    _validate_parent_company(repo, merged.get("parent_company_id") or "", doc_id)
    _validate_unique_fields(
        repo,
        company_name=merged.get("company_name", ""),
        abbr=merged.get("abbr", ""),
        company_code=company_code,
        business_registration_number=merged.get("business_registration_number", ""),
        current_id=doc_id,
    )
    if update_data.get("is_default") is True:
        _clear_existing_default_companies(repo, user_sub=user.sub, exclude_id=doc_id)
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "회사가 수정되었습니다"}


@router.post(
    "/{doc_id}/set-default",
    dependencies=[Depends(require_permission("company:write"))],
)
async def set_default_company(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """기본 회사를 전환한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="회사를 찾을 수 없습니다")
    _clear_existing_default_companies(repo, user_sub=user.sub, exclude_id=doc_id)
    repo.update_by_id(doc_id, {"is_default": True, "updated_by": user.sub})
    return {"id": doc_id, "default_company_id": doc_id, "message": "기본 회사가 변경되었습니다"}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("company:delete"))]
)
async def delete_company(doc_id: str, user: CurrentUserDep) -> None:
    """회사를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="회사를 찾을 수 없습니다")
    if repo.count({"parent_company_id": doc_id}) > 0:
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="하위 회사가 연결된 회사는 삭제할 수 없습니다",
        )
    if doc.get("is_default"):
        sibling_companies = [
            company
            for company in repo.find_many(limit=50, sort=[("created_at", 1)])
            if company.get("_id") != doc_id
        ]
        if sibling_companies:
            raise OneERPError(
                status_code=422,
                error="validation_error",
                detail="기본 회사는 다른 회사를 기본값으로 전환한 뒤 삭제할 수 있습니다",
            )

    repo.delete_by_id(doc_id)
