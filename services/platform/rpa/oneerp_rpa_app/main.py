"""OneERP RPA 서비스.

Appium 기반 모바일 앱 자동화(홈택스/뱅킹/보험)를 관리한다.
RPA 작업 생성·실행·추적, 결과 기록을 제공한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.rpa_tasks import router as rpa_tasks_router

app = create_service_app(
    service_name="rpa",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        rpa_tasks_router,
    ],
)
