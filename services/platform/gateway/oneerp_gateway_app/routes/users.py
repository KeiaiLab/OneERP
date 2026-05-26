"""사용자(User) 워크벤치 라우트."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_tenant_admin

from ..dto import UserCreate, UserUpdate
from ..services import user_service

router = APIRouter(
    prefix="/api/v1/users",
    tags=["사용자"],
    dependencies=[Depends(require_tenant_admin())],
)


@router.post("", status_code=201)
async def create_user(body: UserCreate, user: CurrentUserDep) -> dict[str, Any]:
    """사용자를 생성한다."""
    return user_service.create_user(
        tenant_id=user.tenant_id,
        actor_sub=user.sub,
        body=body,
    )


@router.get("")
async def list_users(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
    *,
    active_only: bool = False,
    status_badge: str | None = None,
    company_id: str | None = None,
    auth_provider: str | None = None,
) -> dict[str, Any]:
    """사용자 목록을 워크벤치 요약과 함께 조회한다."""
    return user_service.list_users(
        tenant_id=user.tenant_id,
        page=page,
        page_size=page_size,
        active_only=active_only,
        status_badge=status_badge,
        company_id=company_id,
        auth_provider=auth_provider,
    )


@router.get("/{doc_id}/summary")
async def get_user_summary(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """사용자 상세 워크벤치 요약을 반환한다."""
    return user_service.get_user_summary(tenant_id=user.tenant_id, doc_id=doc_id)


@router.get("/{doc_id}")
async def get_user(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """사용자 상세 정보를 조회한다."""
    return user_service.get_user(tenant_id=user.tenant_id, doc_id=doc_id)


@router.put("/{doc_id}")
async def update_user(doc_id: str, body: UserUpdate, user: CurrentUserDep) -> dict[str, Any]:
    """사용자를 수정한다."""
    return user_service.update_user(
        tenant_id=user.tenant_id,
        actor_sub=user.sub,
        doc_id=doc_id,
        body=body,
    )


@router.delete("/{doc_id}", status_code=204)
async def delete_user(doc_id: str, user: CurrentUserDep) -> None:
    """비활성 사용자만 삭제한다."""
    user_service.delete_user(tenant_id=user.tenant_id, doc_id=doc_id)
