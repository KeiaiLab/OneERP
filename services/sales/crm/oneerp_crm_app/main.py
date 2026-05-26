"""OneERP CRM 서비스.

커스텀 라우트와 EntityMeta 기반 자동 CRUD를 혼합하여 사용한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.activities import router as activities_router
from .routes.campaigns import router as campaigns_router
from .routes.issue_types import router as issue_types_router
from .routes.issues import router as issues_router
from .routes.knowledge_bases import router as knowledge_bases_router
from .routes.leads import router as leads_router
from .routes.opportunities import router as opportunities_router
from .routes.sales_pipelines import router as sales_pipelines_router
from .routes.service_level_agreements import router as service_level_agreements_router
from .routes.services import router as services_router
from .routes.sla_fulfillments import router as sla_fulfillments_router

app = create_service_app(
    service_name="crm",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        leads_router,
        opportunities_router,
        issues_router,
        issue_types_router,
        activities_router,
        campaigns_router,
        sales_pipelines_router,
        service_level_agreements_router,
        sla_fulfillments_router,
        knowledge_bases_router,
        services_router,
    ],
)
