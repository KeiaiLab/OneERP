"""채널(Channel) CRUD 라우트.

M3 arch-baseline 감소: Route → Service 3층 (sla_fulfillments 패턴 동일).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.permissions import require_permission

from ..models.channel import ChannelCreate, ChannelUpdate
from ..services.channel_service import ChannelService

router = APIRouter(prefix="/api/v1/channels", tags=["채널"])


@router.post("/", status_code=201, dependencies=[Depends(require_permission("channel:create"))])
async def create_channel(body: ChannelCreate, user: CurrentUserDep) -> dict[str, Any]:
    """채널을 생성한다."""
    service = ChannelService(tenant_id=user.tenant_id)
    return service.create_channel_from_request(body)


@router.get("/", dependencies=[Depends(require_permission("channel:read"))])
async def list_channels(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """채널 목록을 페이지네이션으로 조회한다."""
    service = ChannelService(tenant_id=user.tenant_id)
    skip = (page - 1) * page_size
    result = service.list_channels(skip=skip, limit=page_size)
    return {**result, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("channel:read"))])
async def get_channel(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """채널 상세 정보를 조회한다."""
    service = ChannelService(tenant_id=user.tenant_id)
    doc = service.get_channel(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="채널을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("channel:write"))])
async def update_channel(doc_id: str, body: ChannelUpdate, user: CurrentUserDep) -> dict[str, Any]:
    """채널을 수정한다."""
    service = ChannelService(tenant_id=user.tenant_id)
    ok = service.update_channel_fields(doc_id, body.model_dump(exclude_none=True))
    if not ok:
        raise OneERPError(status_code=404, error="not_found", detail="채널을 찾을 수 없습니다")
    return {"message": "채널이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("channel:delete"))])
async def delete_channel(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """채널을 삭제한다."""
    service = ChannelService(tenant_id=user.tenant_id)
    ok = service.delete_channel(doc_id)
    if not ok:
        raise OneERPError(status_code=404, error="not_found", detail="채널을 찾을 수 없습니다")
    return {"message": "채널이 삭제되었습니다"}
