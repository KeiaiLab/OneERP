"""영업파이프라인(SalesPipeline) 조회 라우트 — Report.

M3 arch-baseline 감소: Route → Service 3층으로 정리.
- Repository 직접 호출 제거 → PipelineService.list_pipelines 위임
- `from oneerp_core.repository import Repository` import 제거
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission

from oneerp_crm_app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/api/v1/sales-pipelines", tags=["영업파이프라인"])


@router.get("/", dependencies=[Depends(require_permission("sales_pipeline:read"))])
async def list_sales_pipelines(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """영업파이프라인 목록을 페이지네이션으로 조회한다."""
    service = PipelineService(tenant_id=user.tenant_id)
    skip = (page - 1) * page_size
    result = service.list_pipelines(skip=skip, limit=page_size)
    return {**result, "page": page, "page_size": page_size}


@router.get("/summary", dependencies=[Depends(require_permission("sales_pipeline:read"))])
def get_pipeline_summary(user: CurrentUserDep) -> dict[str, Any]:
    """파이프라인 단계별 요약을 조회한다."""
    service = PipelineService(tenant_id=user.tenant_id)
    return service.get_pipeline_summary()


@router.get(
    "/conversion-metrics",
    dependencies=[Depends(require_permission("sales_pipeline:read"))],
)
def get_conversion_metrics(user: CurrentUserDep) -> dict[str, Any]:
    """리드→기회, 기회→성사 전환율을 조회한다."""
    service = PipelineService(tenant_id=user.tenant_id)
    return service.get_conversion_metrics()
