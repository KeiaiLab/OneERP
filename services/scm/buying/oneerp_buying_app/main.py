"""OneERP 구매(Buying) 서비스.

4개 엔티티는 EntityMeta 기반 자동 CRUD,
9개 엔티티는 커스텀 라우트로 직접 관리.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.landed_cost_vouchers import router as landed_cost_vouchers_router
from .routes.material_requests import router as material_requests_router
from .routes.purchase_analytics import router as purchase_analytics_router
from .routes.purchase_invoices import router as purchase_invoices_router
from .routes.purchase_orders import router as purchase_orders_router
from .routes.purchase_receipts import router as purchase_receipts_router
from .routes.purchase_returns import router as purchase_returns_router
from .routes.request_for_quotations import router as request_for_quotations_router
from .routes.supplier_quotations import router as supplier_quotations_router
from .routes.suppliers import router as suppliers_router

app = create_service_app(
    service_name="buying",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        suppliers_router,
        purchase_orders_router,
        purchase_invoices_router,
        material_requests_router,
        purchase_receipts_router,
        supplier_quotations_router,
        purchase_returns_router,
        request_for_quotations_router,
        landed_cost_vouchers_router,
        purchase_analytics_router,
    ],
    # 커스텀 라우트에서 submit_with_event()를 사용하는 컬렉션
    outbox_collections=[
        "purchase_orders",
        "purchase_invoices",
        "purchase_receipts",
        "material_requests",
    ],
)
