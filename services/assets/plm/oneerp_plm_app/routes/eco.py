"""설계 변경 요청(ECO) API 라우터."""

from __future__ import annotations

from typing import Any, cast

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_plm_app.models.eng_change_order import ECOCreate, EngChangeOrder
from oneerp_plm_app.services.eco_service import ECOService

router = APIRouter(prefix="/api/v1/plm/eco", tags=["PLM ECO"])

_COLLECTION = "eng_change_orders"
_PREFIX = "ECO"


def _get_repo(tenant_id: str) -> Repository:
    """테넌트 기반 Repository를 생성한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post("", status_code=201, dependencies=[Depends(require_permission("plm_eco:create"))])
def ECO_생성(body: ECOCreate, user: CurrentUserDep) -> dict[str, Any]:
    """ECO를 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    doc = EngChangeOrder(
        _id=doc_id,
        tenant_id=user.tenant_id,
        eco_number=doc_id,
        title=body.title,
        description=body.description,
        change_type=body.change_type,
        priority=body.priority,
        is_emergency=body.is_emergency,
        requested_by=user.sub,
        affected_products=body.affected_products,
        affected_bom_versions=body.affected_bom_versions,
        proposed_changes=body.proposed_changes,
        cost_impact=body.cost_impact,
        target_effective_date=body.target_effective_date,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(doc)
    return {"id": doc_id, "message": "ECO가 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("plm_eco:read"))])
def ECO_목록(
    user: CurrentUserDep,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """ECO 목록을 조회한다."""
    repo = _get_repo(user.tenant_id)
    query: dict[str, Any] = {}
    if status:
        query["status"] = status
    skip = (page - 1) * page_size
    items = repo.find_many(query, skip=skip, limit=page_size)
    return {"items": items, "page": page, "page_size": page_size}


@router.get("/{eco_id}", dependencies=[Depends(require_permission("plm_eco:read"))])
def ECO_상세(eco_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """ECO 상세를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(eco_id)
    if not doc:
        raise_not_found(f"ECO를 찾을 수 없습니다: {eco_id}")
    return cast("dict[str, Any]", doc)


@router.post(
    "/{eco_id}/submit",
    dependencies=[Depends(require_permission("plm_eco:write"))],
)
def ECO_제출(eco_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """ECO를 제출한다."""
    service = ECOService(tenant_id=user.tenant_id)
    return service.submit_eco(eco_id)


@router.post(
    "/{eco_id}/assign-reviewers",
    dependencies=[Depends(require_permission("plm_eco:write"))],
)
def ECO_검토자_배정(eco_id: str, body: dict[str, Any], user: CurrentUserDep) -> dict[str, Any]:
    """ECO에 검토자를 배정한다."""
    service = ECOService(tenant_id=user.tenant_id)
    return service.assign_reviewers(eco_id, body.get("reviewers", []))


@router.post(
    "/{eco_id}/review",
    dependencies=[Depends(require_permission("plm_eco:write"))],
)
def ECO_검토(eco_id: str, body: dict[str, Any], user: CurrentUserDep) -> dict[str, Any]:
    """ECO 검토를 제출한다."""
    service = ECOService(tenant_id=user.tenant_id)
    return service.submit_review(
        eco_id=eco_id,
        reviewer_id=body.get("reviewer_id", user.sub),
        review_status=body.get("review_status", ""),
        review_comment=body.get("review_comment", ""),
    )


@router.post(
    "/{eco_id}/approve",
    dependencies=[Depends(require_permission("plm_eco:write"))],
)
def ECO_승인(eco_id: str, body: dict[str, Any], user: CurrentUserDep) -> dict[str, Any]:
    """ECO를 최종 승인한다."""
    service = ECOService(tenant_id=user.tenant_id)
    return service.approve_eco(eco_id, body.get("approved_by", user.sub))


@router.post(
    "/{eco_id}/analyze-impact",
    dependencies=[Depends(require_permission("plm_eco:read"))],
)
def ECO_영향도_분석(eco_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """ECO 영향도를 분석한다."""
    service = ECOService(tenant_id=user.tenant_id)
    return service.analyze_impact(eco_id)
