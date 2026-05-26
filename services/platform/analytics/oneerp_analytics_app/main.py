"""analytics 서비스 앱 엔트리포인트."""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS

app = create_service_app(
    service_name="analytics",
    entity_metas=ENTITY_METAS,
)
