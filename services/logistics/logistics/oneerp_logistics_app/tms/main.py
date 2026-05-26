"""OneERP 운송관리(TMS) 서비스.

8개 엔티티는 EntityMeta 기반 자동 CRUD,
3개 엔티티는 커스텀 라우트로 직접 관리.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.delivery_orders import router as delivery_orders_router
from .routes.freight_settlements import router as freight_settlements_router
from .routes.shipments import router as shipments_router

app = create_service_app(
    service_name="tms",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        shipments_router,
        delivery_orders_router,
        freight_settlements_router,
    ],
)
