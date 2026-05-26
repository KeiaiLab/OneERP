"""사회보험(SocialInsurance) API 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.document import DocStatus
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from oneerp_payroll_app.models.social_insurance import (
    SocialInsurance,
    SocialInsuranceCreate,
    SocialInsuranceUpdate,
)

router = APIRouter(prefix="/api/v1/social-insurances", tags=["사회보험"])

_COLLECTION = "social_insurances"
_PREFIX = "SI"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("social_insurance:create"))]
)
def create_social_insurance(
    body: SocialInsuranceCreate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """사회보험 기록을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    insurance = SocialInsurance(
        _id=doc_id,
        tenant_id=user.tenant_id,
        employee_id=body.employee_id,
        period=body.period,
        national_pension=body.national_pension,
        health_insurance=body.health_insurance,
        employment_insurance=body.employment_insurance,
        industrial_accident=body.industrial_accident,
        total=body.total,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(insurance)
    return {"id": doc_id, "message": "사회보험 기록이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("social_insurance:read"))])
def list_social_insurances(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """사회보험 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    docs = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = repo.count()
    return {
        "data": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("social_insurance:read"))])
def get_social_insurance(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """사회보험 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("사회보험 기록을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("social_insurance:write"))])
def update_social_insurance(
    doc_id: str,
    body: SocialInsuranceUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """사회보험 기록을 수정한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("사회보험 기록을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    if doc.get("docstatus", 0) != DocStatus.DRAFT:
        raise_bad_request("초안 상태에서만 수정할 수 있습니다")

    update_data = body.model_dump(exclude_none=True)
    update_data["updated_by"] = user.sub
    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "사회보험 기록이 수정되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("social_insurance:delete"))],
)
def delete_social_insurance(doc_id: str, user: CurrentUserDep) -> None:
    """사회보험 기록을 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise_not_found("사회보험 기록을 찾을 수 없습니다")
    assert doc is not None  # ty 타입 내로잉 보조
    repo.delete_by_id(doc_id)
