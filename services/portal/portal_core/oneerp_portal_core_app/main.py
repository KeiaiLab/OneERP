"""Portal Core FastAPI 앱 — portal + messenger 통합."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .messenger.entities import ENTITY_METAS as MSG_ENTITY_METAS
from .messenger.routes.channels import router as channels_router
from .messenger.routes.messages import router as messages_router
from .portal.entities import ENTITY_METAS as PORTAL_ENTITY_METAS
from .portal.routes.portal_routes import router as portal_router

ENTITY_METAS = [*PORTAL_ENTITY_METAS, *MSG_ENTITY_METAS]


app = create_service_app(
    service_name="portal-core",
    entity_metas=ENTITY_METAS,
    extra_routers=[portal_router, channels_router, messages_router],
)
