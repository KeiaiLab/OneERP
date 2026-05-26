"""OneERP GTM(글로벌무역관리) 서비스.

무역협정, HS 분류, 수출허가, 수출통제 준수점검, 원산지증명서를 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.compliance import router as compliance_router

app = create_service_app(
    service_name="gtm",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        compliance_router,
    ],
)
