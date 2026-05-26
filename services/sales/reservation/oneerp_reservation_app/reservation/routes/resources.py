"""자원(Resource) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.resource import Resource, ResourceCreate, ResourceUpdate
from ..services.resource_service import ResourceService

router = APIRouter(prefix="/api/v1/resources", tags=["자원"])
_COLLECTION = "resources"
_PREFIX = "RSC"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post(
    "/",
    status_code=201,
    dependencies=[Depends(require_permission("resource:create"))],
)
async def create_resource(body: ResourceCreate) -> dict:
    """자원을 생성한다.

    BR-RSV-001: 자원명 고유성 검증.
    """
    repo = _get_repo()
    svc = ResourceService(tenant_id="default")
    svc.validate_unique_name(body.name)

    doc_id = generate_name(_PREFIX)
    doc = Resource(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"id": doc_id, "message": "자원이 생성되었습니다"}


@router.get(
    "/",
    dependencies=[Depends(require_permission("resource:read"))],
)
async def list_resources(page: int = 1, page_size: int = 20) -> dict:
    """자원 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get(
    "/{doc_id}",
    dependencies=[Depends(require_permission("resource:read"))],
)
async def get_resource(doc_id: str) -> dict:
    """자원 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404,
            error="ERR-RSV-005",
            detail="자원을 찾을 수 없습니다",
        )
    return doc


@router.put(
    "/{doc_id}",
    dependencies=[Depends(require_permission("resource:write"))],
)
async def update_resource(doc_id: str, body: ResourceUpdate) -> dict:
    """자원을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404,
            error="ERR-RSV-005",
            detail="자원을 찾을 수 없습니다",
        )

    update_data = body.model_dump(exclude_none=True)

    # 이름 변경 시 고유성 재검증
    if "name" in update_data:
        svc = ResourceService(tenant_id="default")
        svc.validate_unique_name(update_data["name"], exclude_id=doc_id)

    repo.update_by_id(doc_id, update_data)
    return {"message": "자원이 수정되었습니다"}


@router.post(
    "/{doc_id}/deactivate",
    dependencies=[Depends(require_permission("resource:write"))],
)
async def deactivate_resource(doc_id: str) -> dict:
    """자원을 비활성화한다.

    BR-RSV-002: 활성 예약이 없을 때만 비활성화 가능.
    """
    svc = ResourceService(tenant_id="default")
    return svc.deactivate_resource(doc_id)
