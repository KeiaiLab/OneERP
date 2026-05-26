"""OneERP 마케팅자동화(Marketing Automation) 서비스.

캠페인, 오디언스 세그먼트, 이메일 템플릿, 자동화 워크플로우, 캠페인 분석을 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.campaign_execution import router as campaign_execution_router

app = create_service_app(
    service_name="marketing-automation",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        campaign_execution_router,
    ],
)
