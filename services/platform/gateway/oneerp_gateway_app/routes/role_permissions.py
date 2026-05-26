"""역할권한(RolePermission) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_tenant_admin
from oneerp_core.repository import Repository

from ..models.role_permission import RolePermission, RolePermissionCreate, RolePermissionUpdate

router = APIRouter(
    prefix="/api/v1/role-permissions",
    tags=["역할권한"],
    dependencies=[Depends(require_tenant_admin())],
)
_COLLECTION = "role_permissions"
_PREFIX = "RPERM"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post("", status_code=201)
async def create_role_permission(body: RolePermissionCreate) -> dict:
    """역할권한을 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = RolePermission(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"role_permission_id": doc_id, "message": "역할권한이 생성되었습니다"}


@router.get("")
async def list_role_permissions(page: int = 1, page_size: int = 20) -> dict:
    """역할권한 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}")
async def get_role_permission(doc_id: str) -> dict:
    """역할권한 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="역할권한을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}")
async def update_role_permission(doc_id: str, body: RolePermissionUpdate) -> dict:
    """역할권한을 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="역할권한을 찾을 수 없습니다")
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "역할권한이 수정되었습니다"}


@router.delete("/{doc_id}")
async def delete_role_permission(doc_id: str) -> dict:
    """역할권한을 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="역할권한을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "역할권한이 삭제되었습니다"}
