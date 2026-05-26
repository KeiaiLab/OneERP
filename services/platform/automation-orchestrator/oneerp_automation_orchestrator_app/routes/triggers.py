"""자동화 트리거 생성 라우트."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from pydantic import BaseModel

from oneerp_automation_orchestrator_app.services.trigger_service import TriggerService

router = APIRouter(prefix="/api/v1/automations", tags=["자동화 트리거"])
trigger_service = TriggerService()


class TriggerCreateRequest(BaseModel):
    """자동화 트리거 생성 요청."""

    type: str
    event_name: str | None = None
    debounce_seconds: int | None = None


@router.post(
    "/{automation_id}/triggers",
    status_code=201,
    dependencies=[Depends(require_permission("automation_trigger:create"))],
)
async def create_trigger(
    automation_id: str,
    body: TriggerCreateRequest,
    _user: CurrentUserDep,
) -> dict[str, object]:
    """자동화 트리거를 생성한다."""
    return trigger_service.create_trigger(
        automation_id=automation_id,
        trigger_type=body.type,
        event_name=body.event_name,
        debounce_seconds=body.debounce_seconds,
    )
