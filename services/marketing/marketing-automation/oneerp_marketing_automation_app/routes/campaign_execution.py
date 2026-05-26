"""캠페인 실행 커스텀 라우트."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission

from ..services.campaign_execution_service import CampaignExecutionService

router = APIRouter(prefix="/api/v1/marketing/campaigns", tags=["캠페인"])

logger = logging.getLogger(__name__)


@router.post(
    "/{campaign_id}/start",
    dependencies=[Depends(require_permission("campaign:write"))],
)
async def start_campaign(campaign_id: str, user: CurrentUserDep) -> dict:
    """캠페인을 시작한다."""
    svc = CampaignExecutionService(tenant_id=user.tenant_id)
    return svc.start_campaign(campaign_id)


@router.post(
    "/{campaign_id}/pause",
    dependencies=[Depends(require_permission("campaign:write"))],
)
async def pause_campaign(campaign_id: str, user: CurrentUserDep) -> dict:
    """캠페인을 일시정지한다."""
    svc = CampaignExecutionService(tenant_id=user.tenant_id)
    return svc.pause_campaign(campaign_id)


@router.post(
    "/{campaign_id}/complete",
    dependencies=[Depends(require_permission("campaign:write"))],
)
async def complete_campaign(campaign_id: str, user: CurrentUserDep) -> dict:
    """캠페인을 완료한다."""
    svc = CampaignExecutionService(tenant_id=user.tenant_id)
    return svc.complete_campaign(campaign_id)


@router.get(
    "/{campaign_id}/roi",
    dependencies=[Depends(require_permission("campaign:read"))],
)
async def get_campaign_roi(campaign_id: str, user: CurrentUserDep) -> dict:
    """캠페인 ROI를 조회한다."""
    svc = CampaignExecutionService(tenant_id=user.tenant_id)
    return svc.get_campaign_roi(campaign_id)
