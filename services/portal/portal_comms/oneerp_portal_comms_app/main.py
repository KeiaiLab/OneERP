"""Portal Comms FastAPI 앱 — mail + directory 통합."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .directory.entities import ENTITY_METAS as DIR_ENTITY_METAS
from .directory.routes.directory_search import router as directory_search_router
from .directory.routes.org_tree import router as org_tree_router
from .mail.entities import ENTITY_METAS as MAIL_ENTITY_METAS
from .mail.routes.mail_routes import router as mail_router

ENTITY_METAS = [*MAIL_ENTITY_METAS, *DIR_ENTITY_METAS]


app = create_service_app(
    service_name="portal-comms",
    entity_metas=ENTITY_METAS,
    extra_routers=[mail_router, org_tree_router, directory_search_router],
)
