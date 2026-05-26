"""Learning 클러스터 FastAPI 앱 — lms + workreport 통합 진입점."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .lms.entities import ENTITY_METAS as LMS_ENTITY_METAS
from .lms.events import event_registry as lms_event_registry
from .workreport.entities import ENTITY_METAS as WR_ENTITY_METAS
from .workreport.routes.work_report_comments import router as comments_router
from .workreport.routes.work_report_templates import router as templates_router
from .workreport.routes.work_reports import router as work_reports_router

ENTITY_METAS = [*LMS_ENTITY_METAS, *WR_ENTITY_METAS]


app = create_service_app(
    service_name="learning",
    entity_metas=ENTITY_METAS,
    event_registry=lms_event_registry,
    extra_routers=[
        work_reports_router,
        templates_router,
        comments_router,
    ],
)
