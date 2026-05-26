"""Super Admin 전용 — 테넌트 관리 라우트."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.errors import OneERPError
from oneerp_core.modules import PLAN_DEFAULT_MODULES
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_super_admin
from oneerp_core.repository import Repository
from pydantic import BaseModel, Field

from ..audit_hooks import emit as audit_emit
from ..models.tenant import Tenant, TenantCreate, TenantUpdate
from ..models.user import User, UserTier

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["관리자"],
    dependencies=[Depends(require_super_admin())],
)

_TENANT_COLLECTION = "tenants"
_TENANT_PREFIX = "TNT"
_USER_COLLECTION = "users"
_USER_PREFIX = "USR"


def _get_tenant_repo() -> Repository:
    """테넌트용 Repository (크로스테넌트)."""
    return Repository(_TENANT_COLLECTION)


def _get_user_repo(tenant_id: str = "") -> Repository:
    """사용자용 Repository."""
    if tenant_id:
        return Repository(_USER_COLLECTION, tenant_id=tenant_id)
    return Repository(_USER_COLLECTION)


class ModuleUpdateRequest(BaseModel):
    """모듈 설정 요청 스키마."""

    allowed_modules: list[str] = Field(description="허용 모듈 목록")


class AdminUserCreateRequest(BaseModel):
    """Company Admin 생성 요청 스키마."""

    username: str = Field(description="사용자명")
    email: str = Field(default="", description="이메일")
    full_name: str = Field(default="", description="성명")
    password: str = Field(default="", description="비밀번호")


@router.post("/tenants", status_code=201)
def create_tenant(body: TenantCreate) -> dict[str, Any]:
    """테넌트를 생성한다."""
    repo = _get_tenant_repo()
    doc_id = generate_name(_TENANT_PREFIX)
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


@router.get("/tenants")
def list_tenants(page: int = 1, page_size: int = 20) -> dict[str, Any]:
    """전체 테넌트 목록을 조회한다 (크로스테넌트)."""
    repo = _get_tenant_repo()
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/tenants/{tenant_id}")
def get_tenant(tenant_id: str) -> dict[str, Any]:
    """테넌트 상세 정보를 조회한다."""
    repo = _get_tenant_repo()
    doc = repo.find_by_id(tenant_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="테넌트를 찾을 수 없습니다")
    return doc


@router.put("/tenants/{tenant_id}")
def update_tenant(tenant_id: str, body: TenantUpdate) -> dict[str, Any]:
    """테넌트를 수정한다."""
    repo = _get_tenant_repo()
    doc = repo.find_by_id(tenant_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="테넌트를 찾을 수 없습니다")
    repo.update_by_id(tenant_id, body.model_dump(exclude_none=True))
    audit_emit(
        actor="super_admin",
        action="gateway.update",
        resource=f"tenant/{tenant_id}",
        tenant_id=tenant_id,
        details={"updated_fields": list(body.model_dump(exclude_none=True).keys())},
    )
    return {"message": "테넌트가 수정되었습니다"}


@router.post("/tenants/{tenant_id}/suspend")
def suspend_tenant(tenant_id: str, reason: str = "") -> dict[str, Any]:
    """테넌트를 정지한다."""
    repo = _get_tenant_repo()
    doc = repo.find_by_id(tenant_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="테넌트를 찾을 수 없습니다")
    repo.update_by_id(
        tenant_id,
        {
            "suspended_at": datetime.now(tz=UTC),
            "suspended_reason": reason,
            "is_active": False,
        },
    )
    audit_emit(
        actor="super_admin",
        action="gateway.update",
        resource=f"tenant/{tenant_id}",
        tenant_id=tenant_id,
        details={"action": "suspend", "reason": reason},
    )
    return {"message": "테넌트가 정지되었습니다"}


@router.post("/tenants/{tenant_id}/activate")
def activate_tenant(tenant_id: str) -> dict[str, Any]:
    """테넌트를 활성화한다."""
    repo = _get_tenant_repo()
    doc = repo.find_by_id(tenant_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="테넌트를 찾을 수 없습니다")
    repo.update_by_id(
        tenant_id,
        {
            "suspended_at": None,
            "suspended_reason": "",
            "is_active": True,
        },
    )
    return {"message": "테넌트가 활성화되었습니다"}


@router.put("/tenants/{tenant_id}/modules")
def update_tenant_modules(tenant_id: str, body: ModuleUpdateRequest) -> dict[str, Any]:
    """테넌트의 허용 모듈을 설정한다."""
    repo = _get_tenant_repo()
    doc = repo.find_by_id(tenant_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="테넌트를 찾을 수 없습니다")
    repo.update_by_id(tenant_id, {"allowed_modules": body.allowed_modules})
    return {"message": "모듈 설정이 변경되었습니다", "allowed_modules": body.allowed_modules}


@router.post("/tenants/{tenant_id}/admin-user", status_code=201)
def create_admin_user(tenant_id: str, body: AdminUserCreateRequest) -> dict[str, Any]:
    """테넌트의 Company Admin 사용자를 생성한다."""
    tenant_repo = _get_tenant_repo()
    tenant = tenant_repo.find_by_id(tenant_id)
    if not tenant:
        raise OneERPError(status_code=404, error="not_found", detail="테넌트를 찾을 수 없습니다")

    user_repo = _get_user_repo(tenant_id)
    doc_id = generate_name(_USER_PREFIX)
    password_hash = hashlib.sha256(body.password.encode()).hexdigest() if body.password else ""

    user = User(
        _id=doc_id,
        tenant_id=tenant_id,
        username=body.username,
        email=body.email,
        full_name=body.full_name,
        is_active=True,
        roles=["admin"],
        user_tier=UserTier.TENANT_ADMIN,
        is_super_admin=False,
        password_hash=password_hash,
    )
    user_repo.insert(user)

    # 테넌트에 admin_user_id 설정
    tenant_repo.update_by_id(tenant_id, {"admin_user_id": doc_id})

    return {"user_id": doc_id, "message": "Company Admin이 생성되었습니다"}


@router.get("/stats")
def get_platform_stats() -> dict[str, Any]:
    """플랫폼 전체 통계를 반환한다."""
    tenant_repo = _get_tenant_repo()
    user_repo = Repository(_USER_COLLECTION)

    total_tenants = tenant_repo.count()
    active_tenants = tenant_repo.count({"is_active": True})
    total_users = user_repo.count()

    # 플랜별 테넌트 수
    plan_stats = {}
    for plan in ("starter", "standard", "enterprise"):
        plan_stats[plan] = tenant_repo.count({"plan": plan})

    return {
        "total_tenants": total_tenants,
        "active_tenants": active_tenants,
        "total_users": total_users,
        "plan_distribution": plan_stats,
        "available_modules": PLAN_DEFAULT_MODULES,
    }
