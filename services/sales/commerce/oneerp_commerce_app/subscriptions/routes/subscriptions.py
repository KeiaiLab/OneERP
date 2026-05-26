"""구독 관리 커스텀 라우트 — 활성화·일시정지·해지·재개·청구 엔드포인트."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from pydantic import BaseModel

from ..services.subscription_lifecycle_service import SubscriptionLifecycleService

router = APIRouter(prefix="/api/v1/subscriptions", tags=["구독 관리"])

logger = logging.getLogger(__name__)


class CancelRequest(BaseModel):
    """구독 해지 요청 스키마."""

    reason: str = ""


@router.post(
    "/{sub_id}/activate",
    dependencies=[Depends(require_permission("subscription:write"))],
)
async def activate_subscription(sub_id: str, user: CurrentUserDep) -> dict:
    """구독을 활성화한다."""
    svc = SubscriptionLifecycleService(tenant_id=user.tenant_id)
    return svc.activate(sub_id)


@router.post(
    "/{sub_id}/pause",
    dependencies=[Depends(require_permission("subscription:write"))],
)
async def pause_subscription(sub_id: str, user: CurrentUserDep) -> dict:
    """구독을 일시정지한다."""
    svc = SubscriptionLifecycleService(tenant_id=user.tenant_id)
    return svc.pause(sub_id)


@router.post(
    "/{sub_id}/resume",
    dependencies=[Depends(require_permission("subscription:write"))],
)
async def resume_subscription(sub_id: str, user: CurrentUserDep) -> dict:
    """구독을 재개한다."""
    svc = SubscriptionLifecycleService(tenant_id=user.tenant_id)
    return svc.resume(sub_id)


@router.post(
    "/{sub_id}/cancel",
    dependencies=[Depends(require_permission("subscription:write"))],
)
async def cancel_subscription(sub_id: str, body: CancelRequest, user: CurrentUserDep) -> dict:
    """구독을 해지한다."""
    svc = SubscriptionLifecycleService(tenant_id=user.tenant_id)
    return svc.cancel(sub_id, reason=body.reason)


@router.post(
    "/{sub_id}/generate-invoice",
    dependencies=[Depends(require_permission("subscription_invoice:create"))],
)
async def generate_subscription_invoice(sub_id: str, user: CurrentUserDep) -> dict:
    """구독 청구서를 생성한다."""
    svc = SubscriptionLifecycleService(tenant_id=user.tenant_id)
    return svc.generate_invoice(sub_id)
