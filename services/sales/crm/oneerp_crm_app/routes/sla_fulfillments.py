"""SLA달성(SLAFulfillment) 조회 라우트 — Report.

M3 arch-baseline 감소: Route → Service 3층 (sales_pipelines 패턴 동일).
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.errors import raise_bad_request
from oneerp_core.permissions import require_permission

from oneerp_crm_app.services.sla_service import SLAService

router = APIRouter(prefix="/api/v1/sla-fulfillments", tags=["SLA달성"])


@router.get("/", dependencies=[Depends(require_permission("sla_fulfillment:read"))])
async def list_sla_fulfillments(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """SLA달성 목록을 페이지네이션으로 조회한다."""
    service = SLAService(tenant_id=user.tenant_id)
    skip = (page - 1) * page_size
    result = service.list_fulfillments(skip=skip, limit=page_size)
    return {**result, "page": page, "page_size": page_size}


@router.post(
    "/evaluate/{entity_id}",
    dependencies=[Depends(require_permission("sla_fulfillment:create"))],
)
def evaluate_sla(entity_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """엔티티에 대해 SLA를 평가한다."""
    service = SLAService(tenant_id=user.tenant_id)
    try:
        return service.evaluate_sla(entity_id)
    except ValueError as e:
        raise_bad_request(str(e))


@router.get(
    "/violations",
    dependencies=[Depends(require_permission("sla_fulfillment:read"))],
)
def get_violations(user: CurrentUserDep) -> dict[str, Any]:
    """SLA 위반 건을 조회한다."""
    service = SLAService(tenant_id=user.tenant_id)
    return service.check_violations()


@router.get(
    "/rate",
    dependencies=[Depends(require_permission("sla_fulfillment:read"))],
)
def get_fulfillment_rate(user: CurrentUserDep) -> dict[str, Any]:
    """SLA 이행률을 조회한다."""
    service = SLAService(tenant_id=user.tenant_id)
    return service.get_fulfillment_rate()
