"""portal 서비스 앱 엔트리포인트."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.portal_routes import router as portal_router

app = create_service_app(
    service_name="portal",
    entity_metas=ENTITY_METAS,
    extra_routers=[portal_router],
)
