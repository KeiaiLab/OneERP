"""안전 사고 통계 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.permissions import require_permission

from ..services.incident_stats_service import IncidentStatsService

router = APIRouter(prefix="/api/v1/reports", tags=["EHS 보고서"])


@router.get(
    "/incident-statistics",
    dependencies=[Depends(require_permission("safety_incident:read"))],
)
async def get_incident_statistics() -> dict:
    """안전 사고 통계를 조회한다."""
    service = IncidentStatsService(tenant_id="default")
    return service.get_statistics()
