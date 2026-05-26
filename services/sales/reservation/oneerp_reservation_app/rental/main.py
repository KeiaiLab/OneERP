"""OneERP 렌탈(Rental) 서비스.

5개 엔티티는 EntityMeta 기반 자동 CRUD로 관리한다.
"""

from __future__ import annotations

from oneerp_core.app_factory import create_service_app

from .entities import ENTITY_METAS

app = create_service_app(
    service_name="rental",
    entity_metas=ENTITY_METAS,
)
