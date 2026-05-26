"""OneERP Assets 서비스.

커스텀 라우트와 EntityMeta 기반 자동 CRUD를 혼합하여 사용한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.asset_audits import router as asset_audits_router
from .routes.asset_categories import router as asset_categories_router
from .routes.asset_disposals import router as asset_disposals_router
from .routes.asset_movements import router as asset_movements_router
from .routes.assets import router as assets_router
from .routes.depreciation_entries import router as depreciation_entries_router

app = create_service_app(
    service_name="assets",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        assets_router,
        asset_audits_router,
        asset_categories_router,
        asset_disposals_router,
        asset_movements_router,
        depreciation_entries_router,
    ],
)
