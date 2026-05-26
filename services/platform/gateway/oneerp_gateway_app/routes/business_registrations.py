"""사업자등록(BusinessRegistration) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.business_registration import (
    BusinessRegistration,
    BusinessRegistrationCreate,
    BusinessRegistrationUpdate,
)

router = APIRouter(prefix="/api/v1/business-registrations", tags=["사업자등록"])
_COLLECTION = "business_registrations"
_PREFIX = "BRN"


def _get_repo(tenant_id: str = "") -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("business_registration:create"))]
)
async def create_business_registration(
    body: BusinessRegistrationCreate, user: CurrentUserDep
) -> dict:
    """사업자등록을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    doc = BusinessRegistration(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"business_registration_id": doc_id, "message": "사업자등록이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("business_registration:read"))])
async def list_business_registrations(
    user: CurrentUserDep, page: int = 1, page_size: int = 20
) -> dict:
    """사업자등록 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("business_registration:read"))])
async def get_business_registration(doc_id: str, user: CurrentUserDep) -> dict:
    """사업자등록 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="사업자등록을 찾을 수 없습니다"
        )
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("business_registration:write"))])
async def update_business_registration(
    doc_id: str, body: BusinessRegistrationUpdate, user: CurrentUserDep
) -> dict:
    """사업자등록을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="사업자등록을 찾을 수 없습니다"
        )
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "사업자등록이 수정되었습니다"}


@router.delete(
    "/{doc_id}", dependencies=[Depends(require_permission("business_registration:delete"))]
)
async def delete_business_registration(doc_id: str, user: CurrentUserDep) -> dict:
    """사업자등록을 삭제한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="사업자등록을 찾을 수 없습니다"
        )
    repo.delete_by_id(doc_id)
    return {"message": "사업자등록이 삭제되었습니다"}
