"""OneERP 제조(Manufacturing) 서비스.

커스텀 로직이 있는 7개 엔티티는 extra_routers로 직접 관리하고,
나머지 15개 엔티티는 EntityMeta로 CRUD 라우터를 자동 생성한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.boms import router as boms_router
from .routes.job_cards import router as job_cards_router
from .routes.operations import router as operations_router
from .routes.production_costs import router as production_costs_router
from .routes.production_plans import router as production_plans_router
from .routes.work_orders import router as work_orders_router
from .routes.workstations import router as workstations_router

app = create_service_app(
    service_name="manufacturing",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        boms_router,
        work_orders_router,
        production_plans_router,
        job_cards_router,
        workstations_router,
        operations_router,
        production_costs_router,
    ],
)
