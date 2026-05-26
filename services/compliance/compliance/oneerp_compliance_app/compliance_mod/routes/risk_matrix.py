"""위험 매트릭스 보고서 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.permissions import require_permission

from ..services.risk_matrix_service import RiskMatrixService

router = APIRouter(prefix="/api/v1/reports", tags=["컴플라이언스 보고서"])


@router.get(
    "/risk-matrix",
    dependencies=[Depends(require_permission("risk_assessment:read"))],
)
async def get_risk_matrix() -> dict:
    """위험 매트릭스를 조회한다."""
    service = RiskMatrixService(tenant_id="default")
    return service.generate_matrix()
