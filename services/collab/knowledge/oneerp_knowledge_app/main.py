"""OneERP Knowledge(지식관리) 서비스.

3개 엔티티는 EntityMeta로 CRUD 라우터를 자동 생성하고,
검색/평가 기능은 별도 라우트로 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.article_actions import portal_router
from .routes.article_actions import router as article_actions_router

app = create_service_app(
    service_name="knowledge",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        article_actions_router,
        portal_router,
    ],
)
