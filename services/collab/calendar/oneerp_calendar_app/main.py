"""OneERP 캘린더(Calendar) 서비스.

4개 엔티티는 EntityMeta 기반 자동 CRUD,
3개 엔티티는 커스텀 라우트로 직접 관리.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.calendar_events import router as calendar_events_router
from .routes.holidays import router as holidays_router
from .routes.resource_bookings import router as resource_bookings_router

app = create_service_app(
    service_name="calendar",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        calendar_events_router,
        resource_bookings_router,
        holidays_router,
    ],
)
