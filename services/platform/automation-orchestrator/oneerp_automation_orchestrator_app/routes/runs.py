"""자동화 실행 시작 라우트."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from pydantic import BaseModel, Field

from oneerp_automation_orchestrator_app.services.execution_service import ExecutionService

router = APIRouter(prefix="/api/v1/automations", tags=["자동화 실행"])
execution_service = ExecutionService()


class AutomationRunCreateRequest(BaseModel):
    """자동화 실행 시작 요청."""

    input_params: dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"


@router.post(
    "/{automation_id}/runs",
    status_code=202,
    dependencies=[Depends(require_permission("automation_run:create"))],
)
async def create_run(
    automation_id: str,
    body: AutomationRunCreateRequest,
    _user: CurrentUserDep,
) -> dict[str, object]:
    """자동화 실행을 큐에 등록한다."""
    run = execution_service.enqueue(
        automation_id=automation_id,
        version=1,
        input_params=body.input_params,
        priority=body.priority,
    )
    return {
        "automation_id": run["automation_id"],
        "input_params": run["input_params"],
        "priority": run["priority"],
        "status": run["status"],
        "run_id": run["run_id"],
    }
