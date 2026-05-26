"""알림 템플릿(NotificationTemplate) CRUD 라우터."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.notification import (
    NotificationTemplate,
    NotificationTemplateCreate,
    NotificationTemplateUpdate,
)

router = APIRouter(prefix="/api/v1/notification-templates", tags=["알림 템플릿"])

_COLLECTION = "notification_templates"
_PREFIX = "NOTIF"


def _get_repo(tenant_id: str) -> Repository:
    """현재 사용자의 tenant에 바인딩된 Repository를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("notification_template:create"))]
)
async def create_notification_template(
    body: NotificationTemplateCreate, user: CurrentUserDep
) -> dict[str, Any]:
    """알림 템플릿을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=user.tenant_id)

    template = NotificationTemplate(
        _id=doc_id,
        tenant_id=user.tenant_id,
        name=body.name,
        document_type=body.document_type,
        event=body.event,
        channel=body.channel,
        subject_template=body.subject_template,
        message_template=body.message_template,
        recipients_expression=body.recipients_expression,
        created_by=user.sub,
        updated_by=user.sub,
    )
    repo.insert(template)
    return {"id": doc_id, "message": "알림 템플릿이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("notification_template:read"))])
async def list_notification_templates(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """알림 템플릿 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    docs = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total_count = repo.count()
    return {
        "data": docs,
        "total": total_count,
        "page": page,
        "page_size": page_size,
    }


@router.get("/{doc_id}", dependencies=[Depends(require_permission("notification_template:read"))])
async def get_notification_template(doc_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """알림 템플릿 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="알림 템플릿을 찾을 수 없습니다"
        )
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("notification_template:write"))])
async def update_notification_template(
    doc_id: str,
    body: NotificationTemplateUpdate,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """알림 템플릿을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="알림 템플릿을 찾을 수 없습니다"
        )

    update_data = body.model_dump(exclude_none=True)
    if not update_data:
        raise OneERPError(status_code=400, error="bad_request", detail="수정할 내용이 없습니다")
    update_data["updated_by"] = user.sub

    repo.update_by_id(doc_id, update_data)
    return {"id": doc_id, "message": "알림 템플릿이 수정되었습니다"}


@router.delete(
    "/{doc_id}",
    status_code=204,
    dependencies=[Depends(require_permission("notification_template:delete"))],
)
async def delete_notification_template(doc_id: str, user: CurrentUserDep) -> None:
    """알림 템플릿을 삭제한다. 초안 상태에서만 허용."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(
            status_code=404, error="not_found", detail="알림 템플릿을 찾을 수 없습니다"
        )

    repo.delete_by_id(doc_id)
