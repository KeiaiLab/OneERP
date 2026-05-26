"""수출통제 준수점검 커스텀 라우트."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission

from ..services.compliance_service import ComplianceService

router = APIRouter(prefix="/api/v1/gtm/compliance", tags=["수출통제"])

logger = logging.getLogger(__name__)


@router.post(
    "/screen",
    dependencies=[Depends(require_permission("compliance_check:create"))],
)
async def screen_entity(
    user: CurrentUserDep,
    entity_name: str = "",
    entity_country: str = "",
    check_types: list[str] | None = None,
) -> dict:
    """거래 상대방 스크리닝을 실행한다."""
    svc = ComplianceService(tenant_id=user.tenant_id)
    return svc.screen_entity(entity_name, entity_country, check_types)


@router.get(
    "/export-eligibility",
    dependencies=[Depends(require_permission("compliance_check:read"))],
)
async def check_export_eligibility(
    user: CurrentUserDep,
    item_code: str = "",
    destination_country: str = "",
) -> dict:
    """수출 적격성을 확인한다."""
    svc = ComplianceService(tenant_id=user.tenant_id)
    return svc.check_export_eligibility(item_code, destination_country)
