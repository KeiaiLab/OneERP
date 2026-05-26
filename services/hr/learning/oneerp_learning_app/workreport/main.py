"""OneERP WorkReport(업무일지/보고) 서비스.

3개 엔티티 — WorkReport, WorkReportTemplate, WorkReportComment.
모두 커스텀 비즈니스 로직(제출/승인/반려/취소/통계)이 있어
extra_routers로 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry
from .routes.work_report_comments import router as comments_router
from .routes.work_report_templates import router as templates_router
from .routes.work_reports import router as work_reports_router

app = create_service_app(
    service_name="workreport",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
    extra_routers=[
        work_reports_router,
        templates_router,
        comments_router,
    ],
)
