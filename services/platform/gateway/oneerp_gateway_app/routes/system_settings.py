"""시스템설정(SystemSettings) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.system_settings import SystemSettings, SystemSettingsCreate, SystemSettingsUpdate

router = APIRouter(prefix="/api/v1/system-settings", tags=["시스템설정"])
_COLLECTION = "system_settings"
_PREFIX = "SYSS"


def _get_repo(tenant_id: str = "") -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("system_settings:create"))]
)
async def create_system_settings(body: SystemSettingsCreate, user: CurrentUserDep) -> dict:
    """시스템설정을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    doc = SystemSettings(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"system_settings_id": doc_id, "message": "시스템설정이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("system_settings:read"))])
async def list_system_settings(user: CurrentUserDep, page: int = 1, page_size: int = 20) -> dict:
    """시스템설정 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("system_settings:read"))])
async def get_system_settings(doc_id: str, user: CurrentUserDep) -> dict:
    """시스템설정 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="시스템설정을 찾을 수 없습니다"
        )
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("system_settings:write"))])
async def update_system_settings(
    doc_id: str, body: SystemSettingsUpdate, user: CurrentUserDep
) -> dict:
    """시스템설정을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="시스템설정을 찾을 수 없습니다"
        )
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "시스템설정이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("system_settings:delete"))])
async def delete_system_settings(doc_id: str, user: CurrentUserDep) -> dict:
    """시스템설정을 삭제한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="시스템설정을 찾을 수 없습니다"
        )
    repo.delete_by_id(doc_id)
    return {"message": "시스템설정이 삭제되었습니다"}
