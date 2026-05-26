"""서비스수준협약(ServiceLevelAgreement) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.service_level_agreement import (
    ServiceLevelAgreement,
    ServiceLevelAgreementCreate,
    ServiceLevelAgreementUpdate,
)

router = APIRouter(prefix="/api/v1/service-level-agreements", tags=["SLA"])
_COLLECTION = "service_level_agreements"
_PREFIX = "SLA"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(require_permission("service_level_agreement:create"))],
)
async def create_service_level_agreement(
    body: ServiceLevelAgreementCreate,
) -> dict:
    """SLA를 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = ServiceLevelAgreement(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"service_level_agreement_id": doc_id, "message": "SLA가 생성되었습니다"}


@router.get("/", dependencies=[Depends(require_permission("service_level_agreement:read"))])
async def list_service_level_agreements(page: int = 1, page_size: int = 20) -> dict:
    """SLA 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("service_level_agreement:read"))])
async def get_service_level_agreement(doc_id: str) -> dict:
    """SLA 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="SLA를 찾을 수 없습니다")
    return doc


@router.put(
    "/{doc_id}", dependencies=[Depends(require_permission("service_level_agreement:write"))]
)
async def update_service_level_agreement(doc_id: str, body: ServiceLevelAgreementUpdate) -> dict:
    """SLA를 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="SLA를 찾을 수 없습니다")
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "SLA가 수정되었습니다"}


@router.delete(
    "/{doc_id}", dependencies=[Depends(require_permission("service_level_agreement:delete"))]
)
async def delete_service_level_agreement(doc_id: str) -> dict:
    """SLA를 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="SLA를 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "SLA가 삭제되었습니다"}
