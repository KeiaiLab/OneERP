"""OneERP 설비보전(Maintenance) 서비스.

EntityMeta 기반 자동 CRUD를 사용한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS

app = create_service_app(
    service_name="maintenance",
    entity_metas=ENTITY_METAS,
)
