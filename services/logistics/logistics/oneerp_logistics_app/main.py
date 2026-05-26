"""Logistics FastAPI 앱 — tms + fleet 통합."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .fleet.entities import ENTITY_METAS as FLEET_ENTITY_METAS
from .fleet.routes.vehicle_tco import router as vehicle_tco_router
from .tms.entities import ENTITY_METAS as TMS_ENTITY_METAS
from .tms.events import event_registry as tms_event_registry
from .tms.routes.delivery_orders import router as delivery_orders_router
from .tms.routes.freight_settlements import router as freight_settlements_router
from .tms.routes.shipments import router as shipments_router

ENTITY_METAS = [*TMS_ENTITY_METAS, *FLEET_ENTITY_METAS]


app = create_service_app(
    service_name="logistics",
    entity_metas=ENTITY_METAS,
    event_registry=tms_event_registry,
    extra_routers=[
        shipments_router,
        delivery_orders_router,
        freight_settlements_router,
        vehicle_tco_router,
    ],
)
