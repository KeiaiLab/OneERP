"""OneERP 재고(Stock) 서비스.

커스텀 로직이 있는 엔티티는 extra_routers로 직접 관리하고,
나머지 엔티티는 EntityMeta로 CRUD 라우터를 자동 생성한다.
제조 관련 7개 엔티티(BOM, 작업지시, 생산계획, 작업카드, 작업장, 공정, 생산원가)는
manufacturing 서비스로 이관되었다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.batches import router as batches_router
from .routes.item_groups import router as item_groups_router
from .routes.item_prices import router as item_prices_router
from .routes.item_variants import router as item_variants_router
from .routes.items import router as items_router
from .routes.packing_slips import router as packing_slips_router
from .routes.pick_lists import router as pick_lists_router
from .routes.purchase_receipts import router as purchase_receipts_router
from .routes.serial_nos import router as serial_nos_router
from .routes.stock_balances import router as stock_balances_router
from .routes.stock_bins import router as stock_bins_router
from .routes.stock_entries import router as stock_entries_router
from .routes.stock_ledger_entries import router as stock_ledger_entries_router
from .routes.stock_reconciliations import router as stock_reconciliations_router
from .routes.warehouses import router as warehouses_router

app = create_service_app(
    service_name="stock",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        items_router,
        stock_entries_router,
        warehouses_router,
        batches_router,
        stock_reconciliations_router,
        serial_nos_router,
        item_groups_router,
        stock_balances_router,
        pick_lists_router,
        packing_slips_router,
        item_variants_router,
        item_prices_router,
        purchase_receipts_router,
        stock_bins_router,
        stock_ledger_entries_router,
    ],
    # 커스텀 라우트에서 submit_with_event()를 사용하는 컬렉션
    outbox_collections=[
        "stock_entries",
        "stock_reconciliations",
        "purchase_receipts",
    ],
)
