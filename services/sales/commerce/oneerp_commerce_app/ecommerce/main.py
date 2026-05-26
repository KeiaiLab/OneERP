"""OneERP 전자상거래(E-Commerce) 서비스.

마켓플레이스 연동, 주문 동기화, 드롭쉬핑을 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.marketplace_orders import router as marketplace_orders_router

app = create_service_app(
    service_name="ecommerce",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        marketplace_orders_router,
    ],
)
