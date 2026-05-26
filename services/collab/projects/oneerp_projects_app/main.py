"""OneERP Projects 서비스.

커스텀 라우트와 EntityMeta 기반 자동 CRUD를 혼합하여 사용한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.activity_types import router as activity_types_router
from .routes.milestones import router as milestones_router
from .routes.projects import router as projects_router
from .routes.tasks import router as tasks_router
from .routes.timesheets import router as timesheets_router

app = create_service_app(
    service_name="projects",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        projects_router,
        tasks_router,
        timesheets_router,
        milestones_router,
        activity_types_router,
    ],
)
