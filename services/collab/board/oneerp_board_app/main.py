"""board 서비스 앱 엔트리포인트."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.boards import router as boards_router
from .routes.popups import router as popups_router
from .routes.posts import router as posts_router

app = create_service_app(
    service_name="board",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        boards_router,
        posts_router,
        popups_router,
    ],
)
