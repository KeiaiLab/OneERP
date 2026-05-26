"""consolidation 서비스 앱 엔트리포인트."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.consolidation_routes import router as consolidation_router

app = create_service_app(
    service_name="consolidation",
    entity_metas=ENTITY_METAS,
    extra_routers=[consolidation_router],
)
