"""알림규칙(NotificationRule) CRUD 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.notification_rule import (
    NotificationRule,
    NotificationRuleCreate,
    NotificationRuleUpdate,
)

router = APIRouter(prefix="/api/v1/notification-rules", tags=["알림규칙"])
_COLLECTION = "notification_rules"
_PREFIX = "NTFR"


def _get_repo(tenant_id: str = "") -> Repository:
    """Repository 인스턴스를 반환한다."""
    return Repository(_COLLECTION, tenant_id=tenant_id)


@router.post(
    "", status_code=201, dependencies=[Depends(require_permission("notification_rule:create"))]
)
async def create_notification_rule(body: NotificationRuleCreate, user: CurrentUserDep) -> dict:
    """알림규칙을 생성한다."""
    repo = _get_repo(user.tenant_id)
    doc_id = generate_name(_PREFIX)
    doc = NotificationRule(_id=doc_id, **body.model_dump())
    repo.insert(doc)
    return {"notification_rule_id": doc_id, "message": "알림규칙이 생성되었습니다"}


@router.get("", dependencies=[Depends(require_permission("notification_rule:read"))])
async def list_notification_rules(user: CurrentUserDep, page: int = 1, page_size: int = 20) -> dict:
    """알림규칙 목록을 페이지네이션으로 조회한다."""
    repo = _get_repo(user.tenant_id)
    skip = (page - 1) * page_size
    data = repo.find_many(skip=skip, limit=page_size, sort=[("created_at", -1)])
    total = repo.count()
    return {"data": data, "total": total, "page": page, "page_size": page_size}


@router.get("/{doc_id}", dependencies=[Depends(require_permission("notification_rule:read"))])
async def get_notification_rule(doc_id: str, user: CurrentUserDep) -> dict:
    """알림규칙 상세 정보를 조회한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="알림규칙을 찾을 수 없습니다")
    return doc


@router.put("/{doc_id}", dependencies=[Depends(require_permission("notification_rule:write"))])
async def update_notification_rule(
    doc_id: str, body: NotificationRuleUpdate, user: CurrentUserDep
) -> dict:
    """알림규칙을 수정한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="알림규칙을 찾을 수 없습니다")
    repo.update_by_id(doc_id, body.model_dump(exclude_none=True))
    return {"message": "알림규칙이 수정되었습니다"}


@router.delete("/{doc_id}", dependencies=[Depends(require_permission("notification_rule:delete"))])
async def delete_notification_rule(doc_id: str, user: CurrentUserDep) -> dict:
    """알림규칙을 삭제한다."""
    repo = _get_repo(user.tenant_id)
    doc = repo.find_by_id(doc_id)
    if not doc:
        raise OneERPError(status_code=404, error="not_found", detail="알림규칙을 찾을 수 없습니다")
    repo.delete_by_id(doc_id)
    return {"message": "알림규칙이 삭제되었습니다"}
