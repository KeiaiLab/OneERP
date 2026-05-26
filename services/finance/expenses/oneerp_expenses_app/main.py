"""OneERP Expenses 서비스.

5개 엔티티 모두 커스텀 로직(승인/반려, 법인카드 거래 등)이 있어
extra_routers로만 관리한다. (ENTITY_METAS는 빈 목록)
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.corporate_card_transactions import router as corporate_card_transactions_router
from .routes.corporate_cards import router as corporate_cards_router
from .routes.expense_claims import router as expense_claims_router
from .routes.expense_types import router as expense_types_router
from .routes.travel_requests import router as travel_requests_router

app = create_service_app(
    service_name="expenses",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        expense_claims_router,
        expense_types_router,
        corporate_cards_router,
        corporate_card_transactions_router,
        travel_requests_router,
    ],
)
