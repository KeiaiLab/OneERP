"""OneERP Compliance(컴플라이언스) 서비스.

7개 엔티티는 EntityMeta로 CRUD 라우터를 자동 생성하고,
위험 매트릭스 보고서는 별도 라우트로 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.risk_matrix import router as risk_matrix_router

app = create_service_app(
    service_name="compliance",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        risk_matrix_router,
    ],
)
