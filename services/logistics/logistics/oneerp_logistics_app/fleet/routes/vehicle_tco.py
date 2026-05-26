"""차량 TCO 보고서 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.permissions import require_permission

from ..services.tco_service import TcoService

router = APIRouter(prefix="/api/v1/reports", tags=["차량 보고서"])


@router.get(
    "/vehicle-tco/{vehicle_id}",
    dependencies=[Depends(require_permission("vehicle:read"))],
)
async def get_vehicle_tco(vehicle_id: str) -> dict:
    """차량별 TCO(총소유비용)를 조회한다."""
    service = TcoService(tenant_id="default")
    return service.calculate_tco(vehicle_id)
