"""OneERP 판매(Selling) 서비스.

9개 엔티티는 EntityMeta 기반 자동 CRUD,
10개 엔티티는 커스텀 라우트로 직접 관리.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.blanket_orders import router as blanket_orders_router
from .routes.delivery_notes import router as delivery_notes_router
from .routes.pos_receipts import router as pos_receipts_router
from .routes.pos_transactions import router as pos_transactions_router
from .routes.price_lists import router as price_lists_router
from .routes.quotations import portal_router as portal_quotations_router
from .routes.quotations import router as quotations_router
from .routes.sales_analytics import router as sales_analytics_router
from .routes.sales_invoices import router as sales_invoices_router
from .routes.sales_orders import router as sales_orders_router
from .routes.sales_partners import router as sales_partners_router
from .routes.sales_returns import router as sales_returns_router

app = create_service_app(
    service_name="selling",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        quotations_router,
        portal_quotations_router,
        price_lists_router,
        sales_partners_router,
        sales_orders_router,
        delivery_notes_router,
        sales_invoices_router,
        sales_returns_router,
        blanket_orders_router,
        pos_transactions_router,
        sales_analytics_router,
        pos_receipts_router,
    ],
    # 커스텀 라우트에서 submit_with_event()로 _outbox를 기록하는 컬렉션 목록
    # EntityMeta.submit_event_type 자동 수집에 포함되지 않으므로 명시적으로 추가
    outbox_collections=[
        "sales_orders",
        "delivery_notes",
        "sales_invoices",
        "quotations",
    ],
)
