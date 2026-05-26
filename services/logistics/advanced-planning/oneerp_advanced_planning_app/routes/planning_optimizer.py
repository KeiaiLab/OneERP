"""계획 최적화 커스텀 라우트."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission

from ..services.planning_optimizer_service import PlanningOptimizerService

router = APIRouter(prefix="/api/v1/planning", tags=["계획최적화"])

logger = logging.getLogger(__name__)


@router.get(
    "/balance",
    dependencies=[Depends(require_permission("demand_plan:read"))],
)
async def balance_demand_supply(
    user: CurrentUserDep,
    item_code: str = "",
    warehouse: str = "",
) -> dict:
    """수요-공급 밸런싱을 수행한다."""
    svc = PlanningOptimizerService(tenant_id=user.tenant_id)
    return svc.balance_demand_supply(item_code, warehouse)


@router.post(
    "/scenarios/{scenario_id}/run",
    dependencies=[Depends(require_permission("planning_scenario:write"))],
)
async def run_scenario(scenario_id: str, user: CurrentUserDep) -> dict:
    """What-if 시나리오를 실행한다."""
    svc = PlanningOptimizerService(tenant_id=user.tenant_id)
    return svc.run_scenario(scenario_id)


@router.get(
    "/utilization",
    dependencies=[Depends(require_permission("capacity_plan:read"))],
)
async def calculate_utilization(
    user: CurrentUserDep,
    workstation: str = "",
) -> dict:
    """생산능력 가용률을 조회한다."""
    svc = PlanningOptimizerService(tenant_id=user.tenant_id)
    return svc.calculate_utilization(workstation)
