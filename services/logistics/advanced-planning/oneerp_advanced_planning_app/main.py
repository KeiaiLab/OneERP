"""OneERP 고급계획(Advanced Planning) 서비스.

수요계획, 공급계획, 생산능력계획, 스케줄링 규칙, 계획 시나리오를 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.planning_optimizer import router as planning_optimizer_router

app = create_service_app(
    service_name="advanced-planning",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        planning_optimizer_router,
    ],
)
