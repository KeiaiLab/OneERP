"""OneERP EHS(환경안전보건) 서비스.

4개 엔티티는 EntityMeta로 CRUD 라우터를 자동 생성하고,
사고 통계 보고서는 별도 라우트로 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.incident_stats import router as incident_stats_router

app = create_service_app(
    service_name="ehs",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        incident_stats_router,
    ],
)
