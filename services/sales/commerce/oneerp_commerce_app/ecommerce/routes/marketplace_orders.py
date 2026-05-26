"""마켓플레이스 주문 커스텀 라우트 — 동기화·확인 엔드포인트."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from pydantic import BaseModel

from ..services.order_sync_service import OrderSyncService

router = APIRouter(prefix="/api/v1/ecommerce/orders", tags=["전자상거래 주문"])

logger = logging.getLogger(__name__)


class SyncRequest(BaseModel):
    """주문 동기화 요청 스키마."""

    channel_id: str
    external_orders: list[dict[str, Any]] = []


@router.post(
    "/sync",
    dependencies=[Depends(require_permission("marketplace_order:create"))],
)
async def sync_marketplace_orders(body: SyncRequest, user: CurrentUserDep) -> dict:
    """외부 마켓플레이스 주문을 동기화한다."""
    svc = OrderSyncService(tenant_id=user.tenant_id)
    return svc.sync_orders(body.channel_id, body.external_orders)


@router.post(
    "/{order_id}/confirm",
    dependencies=[Depends(require_permission("marketplace_order:write"))],
)
async def confirm_marketplace_order(order_id: str, user: CurrentUserDep) -> dict:
    """마켓플레이스 주문을 확인 상태로 변경한다."""
    svc = OrderSyncService(tenant_id=user.tenant_id)
    return svc.confirm_order(order_id)
