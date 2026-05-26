"""테넌트(Tenant) CRUD 라우트."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.middleware import clear_tenant_cache
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_super_admin
from oneerp_core.repository import Repository
from pydantic import BaseModel, Field

from ..audit_hooks import emit as audit_emit
from ..models.tenant import Tenant, TenantCreate, TenantUpdate


class TenantSuspendRequest(BaseModel):
    """테넌트 정지 요청 스키마."""

    reason: str = Field(description="정지 사유")


router = APIRouter(
    prefix="/api/v1/tenants",
    tags=["테넌트"],
    dependencies=[Depends(require_super_admin())],
)
_COLLECTION = "tenants"
_PREFIX = "TNT"


def _get_repo() -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION)


@router.post("", status_code=201)
async def create_tenant(body: TenantCreate) -> dict:
    """테넌트를 생성한다."""
    repo = _get_repo()
    doc_id = generate_name(_PREFIX)
    doc = Tenant(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    audit_emit(
        actor="super_admin",
        action="gateway.create",
        resource=f"tenant/{doc_id}",
        tenant_id=doc_id,
        details={"name": body.name if hasattr(body, "name") else doc_id},
    )
    return {"tenant_id": doc_id, "message": "테넌트가 생성되었습니다"}


@router.get("")
async def list_tenants(page: int = 1, page_size: int = 20) -> dict:
    """테넌트 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}")
async def get_tenant(doc_id: str) -> dict:
    """테넌트 상세 정보를 조회한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="테넌트를 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}")
async def update_tenant(doc_id: str, body: TenantUpdate) -> dict:
    """테넌트를 수정한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="테넌트를 찾을 수 없습니다")
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    audit_emit(
        actor="super_admin",
        action="gateway.update",
        resource=f"tenant/{doc_id}",
        tenant_id=doc_id,
        details={"updated_fields": list(body.model_dump(exclude_none=True).keys())},
    )
    return {"message": "테넌트가 수정되었습니다"}


@router.delete("/{doc_id}")
async def delete_tenant(doc_id: str) -> dict:
    """테넌트를 삭제한다."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="테넌트를 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    audit_emit(
        actor="super_admin",
        action="gateway.delete",
        resource=f"tenant/{doc_id}",
        tenant_id=doc_id,
        details={"action": "delete"},
    )
    return {"message": "테넌트가 삭제되었습니다"}


@router.post("/{doc_id}/suspend")
async def suspend_tenant(doc_id: str, body: TenantSuspendRequest) -> dict:
    """테넌트를 정지한다 (super_admin 전용)."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="테넌트를 찾을 수 없습니다")
    repo.update_by_id(
        doc_id,
        {
            "suspended_at": datetime.now(UTC),
            "suspended_reason": body.reason,
            "is_active": False,
        },
    )
    clear_tenant_cache()
    return {"message": "테넌트가 정지되었습니다"}


@router.post("/{doc_id}/activate")
async def activate_tenant(doc_id: str) -> dict:
    """정지된 테넌트를 재활성화한다 (super_admin 전용)."""
    repo = _get_repo()
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="테넌트를 찾을 수 없습니다")
    repo.update_by_id(
        doc_id,
        {
            "suspended_at": None,
            "suspended_reason": "",
            "is_active": True,
        },
    )
    clear_tenant_cache()
    return {"message": "테넌트가 활성화되었습니다"}
