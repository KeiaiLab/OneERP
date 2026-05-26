"""메시지(Message) CRUD 라우트.

M3 arch-baseline 감소: Route → Service 3층 (channels 패턴 동일).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.permissions import require_permission

from ..models.message import MessageCreate, MessageUpdate
from ..services.message_service import MessageService

router = APIRouter(prefix="/api/v1/messages", tags=["메시지"])


@router.post("/", status_code=201, dependencies=[Depends(require_permission("message:create"))])
async def create_message(body: MessageCreate, user: CurrentUserDep) -> dict[str, Any]:
    """메시지를 생성한다."""
    service = MessageService(tenant_id=user.tenant_id)
    return service.create_message_from_request(body)


@router.get("/", dependencies=[Depends(require_permission("message:read"))])
async def list_messages(
    user: CurrentUserDep,
    channel_id: str | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict[str, Any]:
    """메시지 목록을 페이지네이션으로 조회한다."""
    service = MessageService(tenant_id=user.tenant_id)
    skip = (page - 1) * page_size
    result = service.list_messages(channel_id=channel_id, skip=skip, limit=page_size)
    return {**result, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("message:read"))])
async def get_message(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """메시지 상세 정보를 조회한다."""
    service = MessageService(tenant_id=user.tenant_id)
    doc = service.get_message(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="메시지를 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("message:write"))])
async def update_message(doc_id: str, body: MessageUpdate, user: CurrentUserDep) -> dict[str, Any]:
    """메시지를 수정한다."""
    service = MessageService(tenant_id=user.tenant_id)
    ok = service.update_message_fields(doc_id, body.model_dump(exclude_none=True))
    if not ok:
        raise OneERPError(status_code=404, error="not_found", detail="메시지를 찾을 수 없습니다")
    return {"message": "메시지가 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("message:delete"))])
async def delete_message(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """메시지를 삭제한다."""
    service = MessageService(tenant_id=user.tenant_id)
    ok = service.hard_delete_message(doc_id)
    if not ok:
        raise OneERPError(status_code=404, error="not_found", detail="메시지를 찾을 수 없습니다")
    return {"message": "메시지가 삭제되었습니다"}
