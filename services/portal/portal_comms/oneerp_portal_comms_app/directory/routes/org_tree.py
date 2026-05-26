"""조직 트리 API 라우터 — 조직 구조 조회/이동/스냅샷."""

from __future__ import annotations

from datetime import date  # noqa: TC003
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request, raise_not_found
from oneerp_core.permissions import require_permission

from oneerp_portal_comms_app.directory.services.org_tree_service import OrgTreeService

router = APIRouter(prefix="/api/v1/org-tree", tags=["조직트리"])


def _get_service(tenant_id: str) -> OrgTreeService:
    """현재 사용자의 tenant에 바인딩된 서비스를 반환한다."""
    return OrgTreeService(tenant_id=tenant_id)


@router.get(
    "/{org_id}",
    dependencies=[Depends(require_permission("org_tree:read"))],
)
def get_org_tree(org_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """조직의 전체 트리 구조를 조회한다."""
    svc = _get_service(user.tenant_id)
    try:
        return svc.get_org_tree(org_id)
    except ValueError as e:
        raise_not_found(str(e))


@router.post(
    "/units/{unit_id}/move",
    dependencies=[Depends(require_permission("org_tree:write"))],
)
def move_unit(
    unit_id: str,
    new_parent_id: str | None,
    user: CurrentUserDep,
) -> dict[str, Any]:
    """조직 단위를 다른 상위 단위로 이동한다."""
    svc = _get_service(user.tenant_id)
    try:
        return svc.move_unit(unit_id, new_parent_id)
    except ValueError as e:
        raise_bad_request(str(e))


@router.post(
    "/{org_id}/snapshot",
    status_code=201,
    dependencies=[Depends(require_permission("org_tree:write"))],
)
def create_snapshot(
    org_id: str,
    user: CurrentUserDep,
    snapshot_date: date | None = None,
    description: str = "",
) -> dict[str, Any]:
    """조직도 스냅샷을 생성한다."""
    svc = _get_service(user.tenant_id)
    try:
        return svc.create_snapshot(org_id, snapshot_date, description)
    except ValueError as e:
        raise_not_found(str(e))
