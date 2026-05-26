"""OneERP 바코드/IoT 서비스.

4개 엔티티는 EntityMeta 기반 자동 CRUD로 관리.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS
from .events import event_registry

app = create_service_app(
    service_name="iot",
    entity_metas=ENTITY_METAS,
    event_registry=event_registry,
)
