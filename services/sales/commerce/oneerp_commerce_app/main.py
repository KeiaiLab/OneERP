"""Commerce FastAPI 앱 — subscriptions + ecommerce 통합."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .ecommerce.entities import ENTITY_METAS as EC_ENTITY_METAS
from .ecommerce.routes.marketplace_orders import router as marketplace_orders_router
from .subscriptions.entities import ENTITY_METAS as SUB_ENTITY_METAS
from .subscriptions.routes.subscriptions import router as subscriptions_router

ENTITY_METAS = [*SUB_ENTITY_METAS, *EC_ENTITY_METAS]


app = create_service_app(
    service_name="commerce",
    entity_metas=ENTITY_METAS,
    extra_routers=[subscriptions_router, marketplace_orders_router],
)
