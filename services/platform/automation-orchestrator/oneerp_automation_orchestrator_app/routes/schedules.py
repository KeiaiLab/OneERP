"""자동화 스케줄 생성 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from pydantic import BaseModel

from oneerp_automation_orchestrator_app.services.schedule_service import ScheduleService

router = APIRouter(prefix="/api/v1/automations", tags=["자동화 스케줄"])
schedule_service = ScheduleService()


class ScheduleCreateRequest(BaseModel):
    """자동화 스케줄 생성 요청."""

    cron: str
    timezone: str


@router.post(
    "/{automation_id}/schedules",
    status_code=201,
    dependencies=[Depends(require_permission("automation_schedule:create"))],
)
async def create_schedule(
    automation_id: str,
    body: ScheduleCreateRequest,
    _user: CurrentUserDep,
) -> dict[str, object]:
    """자동화 스케줄을 생성한다."""
    return schedule_service.create_schedule(
        automation_id=automation_id,
        cron=body.cron,
        timezone=body.timezone,
    )
