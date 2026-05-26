"""OneERP 통합허브(Integration Hub) 서비스.

커넥터, 데이터 매핑, 통합 플로우, 로그, 웹훅 엔드포인트를 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.flow_execution import router as flow_execution_router

app = create_service_app(
    service_name="integration-hub",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        flow_execution_router,
    ],
)
