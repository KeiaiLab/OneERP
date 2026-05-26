"""자동화 정의 생성 라우트."""

from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/automations", tags=["자동화"])


class AutomationCreateRequest(BaseModel):
    """자동화 정의 생성 요청."""

    name: str


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(require_permission("automation_definition:create"))],
)
async def create_automation(
    body: AutomationCreateRequest,
    _user: CurrentUserDep,
) -> dict[str, object]:
    """자동화 정의를 생성한다."""
    return {
        "automation_id": f"AUTO-STUB-{uuid4().hex[:12].upper()}",
        "version": 1,
        "status": "draft",
        "name": body.name,
    }
