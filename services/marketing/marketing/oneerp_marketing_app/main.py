"""OneERP 마케팅(Marketing) 서비스.

이메일/SMS 캠페인, 마케팅 리스트, 행사 관리, 설문조사,
로열티 프로그램을 통합 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.campaigns import router as campaigns_router

app = create_service_app(
    service_name="marketing",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        campaigns_router,
    ],
)
