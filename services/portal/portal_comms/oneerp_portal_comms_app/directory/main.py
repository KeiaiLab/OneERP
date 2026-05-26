"""OneERP 조직도/인명부(Organization Directory) 서비스.

5개 엔티티는 EntityMeta 기반 자동 CRUD,
조직 트리/인명부 검색은 커스텀 라우트로 직접 관리.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.directory_search import router as directory_search_router
from .routes.org_tree import router as org_tree_router

app = create_service_app(
    service_name="directory",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        org_tree_router,
        directory_search_router,
    ],
)
