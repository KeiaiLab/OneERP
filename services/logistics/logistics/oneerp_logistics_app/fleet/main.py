"""OneERP Fleet(차량관리) 서비스.

5개 엔티티는 EntityMeta로 CRUD 라우터를 자동 생성하고,
TCO 보고서는 별도 라우트로 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.vehicle_tco import router as vehicle_tco_router

app = create_service_app(
    service_name="fleet",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        vehicle_tco_router,
    ],
)
