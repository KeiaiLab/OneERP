"""OneERP Reservation(자원 예약) 서비스.

3개 엔티티(Resource, Reservation, ReservationPolicy) 모두
커스텀 로직(시간 충돌 검증, 체크인/아웃 등)이 있어
extra_routers로만 관리한다. (ENTITY_METAS는 빈 목록)
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.reservation_policies import router as reservation_policies_router
from .routes.reservations import router as reservations_router
from .routes.resources import router as resources_router

app = create_service_app(
    service_name="reservation",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        resources_router,
        reservations_router,
        reservation_policies_router,
    ],
)
