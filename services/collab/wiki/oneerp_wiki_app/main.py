"""OneERP 위키(Wiki) 서비스.

6개 엔티티는 EntityMeta 기반 자동 CRUD,
위키 페이지(publish/archive/tree)는 커스텀 라우트로 직접 관리.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.wiki_pages import router as wiki_pages_router

app = create_service_app(
    service_name="wiki",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        wiki_pages_router,
    ],
)
