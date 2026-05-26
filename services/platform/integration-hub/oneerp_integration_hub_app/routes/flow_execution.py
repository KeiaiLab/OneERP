"""통합 플로우 실행 커스텀 라우트."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from pydantic import BaseModel

from ..services.flow_executor_service import FlowExecutorService

router = APIRouter(prefix="/api/v1/integration/flows", tags=["통합플로우"])

logger = logging.getLogger(__name__)


class TransformRequest(BaseModel):
    """데이터 변환 요청 스키마."""

    mapping_id: str
    source_data: list[dict[str, Any]] = []


@router.post(
    "/{flow_id}/execute",
    dependencies=[Depends(require_permission("integration_flow:write"))],
)
async def execute_flow(flow_id: str, user: CurrentUserDep) -> dict:
    """통합 플로우를 실행한다."""
    svc = FlowExecutorService(tenant_id=user.tenant_id)
    return svc.execute_flow(flow_id)


@router.post(
    "/transform",
    dependencies=[Depends(require_permission("data_mapping:read"))],
)
async def transform_data(body: TransformRequest, user: CurrentUserDep) -> dict:
    """데이터 매핑 규칙으로 데이터를 변환한다."""
    svc = FlowExecutorService(tenant_id=user.tenant_id)
    return svc.transform_data(body.mapping_id, body.source_data)
