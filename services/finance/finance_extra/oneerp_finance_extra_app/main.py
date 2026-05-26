"""Finance Extra FastAPI 앱 — consolidation + esg 통합."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .consolidation.entities import ENTITY_METAS as CONS_ENTITY_METAS
from .consolidation.routes.consolidation_routes import router as consolidation_router
from .esg.entities import ENTITY_METAS as ESG_ENTITY_METAS
from .esg.events import event_registry as esg_event_registry

ENTITY_METAS = [*CONS_ENTITY_METAS, *ESG_ENTITY_METAS]


app = create_service_app(
    service_name="finance-extra",
    entity_metas=ENTITY_METAS,
    event_registry=esg_event_registry,
    extra_routers=[consolidation_router],
)
