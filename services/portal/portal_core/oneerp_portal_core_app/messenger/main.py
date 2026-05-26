"""OneERP 사내 메신저(Internal Messenger) 서비스.

커스텀 라우트와 EntityMeta 기반 자동 CRUD를 혼합하여 사용한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .routes.channels import router as channels_router
from .routes.messages import router as messages_router

app = create_service_app(
    service_name="messenger",
    entity_metas=ENTITY_METAS,
    extra_routers=[
        channels_router,
        messages_router,
    ],
)
