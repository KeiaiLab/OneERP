"""OneERP Quality 서비스.

커스텀 로직이 있는 엔티티는 라우트로 직접 관리하고,
나머지 8개 엔티티는 EntityMeta로 CRUD 라우터를 자동 생성한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.inspection_results import router as inspection_results_router
from .routes.non_conformances import router as non_conformances_router
from .routes.quality_goals import router as quality_goals_router
from .routes.quality_inspection_templates import router as quality_inspection_templates_router
from .routes.quality_inspections import router as quality_inspections_router

app = create_service_app(
    service_name="quality",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        quality_inspections_router,
        quality_inspection_templates_router,
        non_conformances_router,
        inspection_results_router,
        quality_goals_router,
    ],
)
