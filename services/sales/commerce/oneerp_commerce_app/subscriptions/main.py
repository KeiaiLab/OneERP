"""OneERP 구독관리(Subscriptions) 서비스.

구독 플랜, 구독 라이프사이클, 자동 청구, 정기 청구를 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.subscriptions import router as subscriptions_router

app = create_service_app(
    service_name="subscriptions",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        subscriptions_router,
    ],
)
