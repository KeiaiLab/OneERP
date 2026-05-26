"""코스트센터(Cost Center) CRUD 라우터."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_conflict, raise_unprocessable
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository
from oneerp_core.route_helpers import delete_draft, get_or_404

from ..models.cost_center import CostCenter, CostCenterCreate, CostCenterUpdate

router = APIRouter(prefix="/api/v1/cost-centers", tags=["코스트센터"])

_COLLECTION = "cost_centers"
_PREFIX = "CC"
_NOT_FOUND = "코스트센터를 찾을 수 없습니다"
_TREE_SORT = [("company", 1), ("cost_center_name", 1), ("created_at", 1)]


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_journal_entry_repo(tenant_id: str) -> Repository:
    """분개전표 참조 무결성 확인용 Repository를 생성한다."""
    return Repository("journal_entries", tenant_id=tenant_id)


def _get_budget_repo(tenant_id: str) -> Repository:
    """예산 참조 무결성 확인용 Repository를 생성한다."""
    return Repository("budgets", tenant_id=tenant_id)


def _validate_parent_cost_center(repo: Repository, parent_cost_center: str | None) -> None:
    """상위 원가센터 존재 여부를 확인한다."""
    if parent_cost_center is None:
        return
    get_or_404(repo, parent_cost_center, "상위 원가센터를 찾을 수 없습니다")


def _find_duplicate_cost_center(
    repo: Repository,
    *,
    cost_center_name: str | None,
    company: str | None,
    exclude_id: str | None = None,
) -> dict[str, Any] | None:
    """같은 회사 내 중복 원가센터명을 찾는다."""
    if not cost_center_name:
        return None
    query: dict[str, Any] = {
        "cost_center_name": cost_center_name,
        "company": company or "",
    }
    if exclude_id:
        query["_id"] = {"$ne": exclude_id}
    duplicates = repo.find_many(query, limit=1, sort=[("created_at", -1)])
    return duplicates[0] if duplicates else None


def _build_cost_center_tree(cost_centers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """원가센터 목록을 부모-자식 트리로 변환한다."""
    children_by_parent: dict[str | None, list[dict[str, Any]]] = defaultdict(list)
    for cost_center in cost_centers:
        children_by_parent[cost_center.get("parent_cost_center")].append(cost_center)

    def _sort_key(cost_center: dict[str, Any]) -> tuple[str, str]:
        return (cost_center.get("company") or "", cost_center.get("cost_center_name") or "")

    for group in children_by_parent.values():
        group.sort(key=_sort_key)

    def _walk(parent_id: str | None) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []
        for cost_center in children_by_parent.get(parent_id, []):
            children = _walk(cost_center["_id"])
            nodes.append({**cost_center, "child_count": len(children), "children": children})
        return nodes

    return _walk(None)


def _cost_center_summary(cost_centers: list[dict[str, Any]]) -> dict[str, Any]:
    """원가센터 요약 집계를 생성한다."""
    company_counter = Counter(
        cost_center.get("company") or "미지정" for cost_center in cost_centers
    )
    group_count = sum(1 for cost_center in cost_centers if cost_center.get("is_group"))
    return {
        "group_count": group_count,
        "leaf_count": len(cost_centers) - group_count,
        "company_counts": dict(company_counter),
    }


def _ensure_cost_center_can_delete(
    cost_center_repo: Repository,
    journal_repo: Repository,
    budget_repo: Repository,
    cost_center_doc: dict[str, Any],
) -> None:
    """하위 원가센터나 참조 문서가 있으면 삭제를 차단한다."""
    cost_center_id = cost_center_doc["_id"]
    if cost_center_repo.count({"parent_cost_center": cost_center_id}) > 0:
        raise_unprocessable("ERR-ACCT-031", "하위 원가센터가 있는 원가센터는 삭제할 수 없습니다")
    if journal_repo.count({"items": {"$elemMatch": {"cost_center": cost_center_id}}}) > 0:
        raise_unprocessable(
            "ERR-ACCT-032", "분개 또는 예산에 사용 중인 원가센터는 삭제할 수 없습니다"
        )
    if budget_repo.count({"cost_center": cost_center_id}) > 0:
        raise_unprocessable(
            "ERR-ACCT-032", "분개 또는 예산에 사용 중인 원가센터는 삭제할 수 없습니다"
        )


@router.post("", status_code=201, dependencies=[Depends(require_permission("cost_center:create"))])
def 코스트센터_생성(body: CostCenterCreate, user: CurrentUserDep) -> dict:
    """코스트센터를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)
    _validate_parent_cost_center(repo, body.parent_cost_center)
    if _find_duplicate_cost_center(
        repo,
        cost_center_name=body.cost_center_name,
        company=body.company,
    ):
        raise_conflict("동일한 회사에 같은 원가센터명이 이미 존재합니다")
    cost_center = CostCenter(
        _id=doc_id,
        tenant_id=user.tenant_id,
        cost_center_name=body.cost_center_name,
        parent_cost_center=body.parent_cost_center,
        is_group=body.is_group,
        company=body.company,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(cost_center)
    return {
        "id": doc_id,
        "_id": doc_id,
        "cost_center_name": body.cost_center_name,
        "parent_cost_center": body.parent_cost_center,
        "company": body.company,
        "is_group": body.is_group,
        "message": "코스트센터 생성 완료",
    }


@router.get("", dependencies=[Depends(require_permission("cost_center:read"))])
def 코스트센터_목록(
    user: CurrentUserDep,
    parent: str | None = None,
    company: str | None = None,
) -> list[dict]:
    """코스트센터 목록을 조회한다. parent 파라미터로 트리 구조를 지원한다."""
    repo = _get_repo(user.tenant_id)
    query: dict = {}
    if parent is not None:
        query["parent_cost_center"] = parent
    if company is not None:
        query["company"] = company
    return repo.find_many(query, limit=200, sort=_TREE_SORT)


@router.get("/tree", dependencies=[Depends(require_permission("cost_center:read"))])
def 코스트센터_트리(user: CurrentUserDep, company: str | None = None) -> dict[str, Any]:
    """원가센터 트리와 회사별 요약을 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if company is not None:
        query["company"] = company
    cost_centers = repo.find_many(query, limit=1000, sort=_TREE_SORT)
    return {
        "data": _build_cost_center_tree(cost_centers),
        "total": len(cost_centers),
        "summary": _cost_center_summary(cost_centers),
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("cost_center:read"))])
def 코스트센터_조회(doc_id: str, user: CurrentUserDep) -> dict:
    """코스트센터를 조회한다."""
    repo = _get_repo(user.tenant_id)
    return get_or_404(repo, doc_id, _NOT_FOUND)


@router.put("/{doc_id}", dependencies=[Depends(require_permission("cost_center:write"))])
def 코스트센터_수정(doc_id: str, body: CostCenterUpdate, user: CurrentUserDep) -> dict:
    """코스트센터를 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    update_data = body.model_dump(exclude_none=True)
    if "parent_cost_center" in update_data:
        _validate_parent_cost_center(repo, update_data["parent_cost_center"])
    if _find_duplicate_cost_center(
        repo,
        cost_center_name=update_data.get("cost_center_name", doc.get("cost_center_name")),
        company=update_data.get("company", doc.get("company")),
        exclude_id=doc_id,
    ):
        raise_conflict("동일한 회사에 같은 원가센터명이 이미 존재합니다")
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {**doc, **update_data}


@router.delete(
    "/{doc_id}", status_code=204, dependencies=[Depends(require_permission("cost_center:delete"))]
)
def 코스트센터_삭제(doc_id: str, user: CurrentUserDep) -> None:
    """코스트센터를 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = get_or_404(repo, doc_id, _NOT_FOUND)
    _ensure_cost_center_can_delete(
        repo,
        _get_journal_entry_repo(user.tenant_id),
        _get_budget_repo(user.tenant_id),
        doc,
    )
    delete_draft(repo, doc_id, _NOT_FOUND)
