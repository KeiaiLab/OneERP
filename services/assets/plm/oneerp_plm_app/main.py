"""OneERP 제품수명주기관리(PLM) 서비스.

7개 엔티티: Product, BOMVersion, ECO는 커스텀 라우트,
ECN, Drawing, Certification, PartApproval은 EntityMeta 기반 CRUD.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.bom_versions import router as bom_versions_router
from .routes.eco import router as eco_router
from .routes.products import router as products_router

app = create_service_app(
    service_name="plm",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        products_router,
        bom_versions_router,
        eco_router,
    ],
)
