"""대시보드 KPI + SSE 스트리밍 라우트.

- GET /api/v1/dashboard/kpis — 현재 테넌트 KPI (JSON)
- GET /api/v1/dashboard/kpis/stream — SSE 스트리밍 (30초 간격)
- GET /api/v1/admin/dashboard/tenants — super_admin 테넌트별 모니터링
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_super_admin

from oneerp_gateway_app.services.dashboard_service import DashboardService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dashboard", tags=["대시보드"])
admin_router = APIRouter(
    prefix="/api/v1/admin/dashboard",
    tags=["관리자 대시보드"],
    dependencies=[Depends(require_super_admin())],
)


@router.get("/kpis")
def get_kpis(user: CurrentUserDep) -> dict[str, Any]:
    """현재 테넌트 KPI를 조회한다."""
    service = DashboardService(user.tenant_id)
    return service.get_kpis_for_user(user.sub)


@router.get("/sales-chart")
def get_sales_chart(user: CurrentUserDep) -> list[dict[str, Any]]:
    """최근 6개월 월별 매출 차트를 반환한다."""
    service = DashboardService(user.tenant_id)
    return service.get_monthly_sales_chart()


@router.get("/kpis/stream")
async def stream_kpis(user: CurrentUserDep) -> StreamingResponse:
    """SSE로 KPI를 스트리밍한다 (30초 간격)."""

    async def _event_generator() -> AsyncGenerator[str]:
        """KPI를 주기적으로 발행하는 SSE 이벤트 생성기."""
        try:
            while True:
                service = DashboardService(user.tenant_id)
                kpis = service.get_kpis_for_user(user.sub)
                data = json.dumps(kpis, default=str, ensure_ascii=False)
                yield f"data: {data}\n\n"
                await asyncio.sleep(30)
        except asyncio.CancelledError:
            logger.info("SSE 스트림 종료: user=%s, tenant=%s", user.sub, user.tenant_id)

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


@admin_router.get("/tenants")
def get_tenant_overview(user: CurrentUserDep) -> dict[str, Any]:
    """super_admin 테넌트별 모니터링 개요를 반환한다."""
    service = DashboardService(user.tenant_id)
    return {"tenants": service.get_tenant_overview()}
