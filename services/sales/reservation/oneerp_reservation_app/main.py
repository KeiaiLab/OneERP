"""Reservation FastAPI 앱 — rental + reservation 통합."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .rental.entities import ENTITY_METAS as RENTAL_ENTITY_METAS
from .reservation.entities import ENTITY_METAS as RES_ENTITY_METAS
from .reservation.events import event_registry as res_event_registry
from .reservation.routes.reservation_policies import router as reservation_policies_router
from .reservation.routes.reservations import router as reservations_router
from .reservation.routes.resources import router as resources_router

ENTITY_METAS = [*RENTAL_ENTITY_METAS, *RES_ENTITY_METAS]


app = create_service_app(
    service_name="reservation",
    entity_metas=ENTITY_METAS,
    event_registry=res_event_registry,
    extra_routers=[
        reservations_router,
        reservation_policies_router,
        resources_router,
    ],
)
