"""QM FastAPI 앱 — maintenance + quality 통합."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .maintenance.entities import ENTITY_METAS as MAINT_ENTITY_METAS
from .quality.entities import ENTITY_METAS as QUAL_ENTITY_METAS
from .quality.routes.inspection_results import router as inspection_results_router
from .quality.routes.non_conformances import router as non_conformances_router
from .quality.routes.quality_goals import router as quality_goals_router
from .quality.routes.quality_inspection_templates import (
    router as quality_inspection_templates_router,
)
from .quality.routes.quality_inspections import router as quality_inspections_router

ENTITY_METAS = [*MAINT_ENTITY_METAS, *QUAL_ENTITY_METAS]


app = create_service_app(
    service_name="qm",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        quality_inspections_router,
        quality_inspection_templates_router,
        non_conformances_router,
        inspection_results_router,
        quality_goals_router,
    ],
)
