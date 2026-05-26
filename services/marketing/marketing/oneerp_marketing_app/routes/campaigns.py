"""캠페인 발송 커스텀 라우트 — 이메일/SMS 캠페인 발송 엔드포인트."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission

from ..services.campaign_service import CampaignService

router = APIRouter(prefix="/api/v1/marketing", tags=["마케팅 캠페인"])

logger = logging.getLogger(__name__)


@router.post(
    "/email-campaigns/{campaign_id}/send",
    dependencies=[Depends(require_permission("email_campaign:write"))],
)
async def send_email_campaign(campaign_id: str, user: CurrentUserDep) -> dict:
    """이메일 캠페인을 발송한다."""
    svc = CampaignService(tenant_id=user.tenant_id)
    return svc.send_email_campaign(campaign_id)


@router.post(
    "/sms-campaigns/{campaign_id}/send",
    dependencies=[Depends(require_permission("sms_campaign:write"))],
)
async def send_sms_campaign(campaign_id: str, user: CurrentUserDep) -> dict:
    """SMS 캠페인을 발송한다."""
    svc = CampaignService(tenant_id=user.tenant_id)
    return svc.send_sms_campaign(campaign_id)
