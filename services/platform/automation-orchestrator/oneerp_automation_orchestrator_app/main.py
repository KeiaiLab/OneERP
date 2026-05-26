"""OneERP Automation Orchestrator 서비스.

최소 스캐폴드만 제공한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from oneerp_automation_orchestrator_app.entities import ENTITY_METAS
from oneerp_automation_orchestrator_app.routes.automations import router as automations_router
from oneerp_automation_orchestrator_app.routes.runs import router as runs_router
from oneerp_automation_orchestrator_app.routes.schedules import router as schedules_router
from oneerp_automation_orchestrator_app.routes.triggers import router as triggers_router

app = create_service_app(
    service_name="automation-orchestrator",
    entity_metas=ENTITY_METAS,
    extra_routers=[automations_router, runs_router, triggers_router, schedules_router],
)
app.title = "OneERP Automation Orchestrator API"
app.description = "OneERP Automation Orchestrator 서비스 REST API"
