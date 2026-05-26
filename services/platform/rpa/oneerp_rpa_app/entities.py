"""RPA 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

RPAResult 엔티티를 EntityMeta로 선언한다.
RPATask는 커스텀 로직(실행/취소 등)이 있으므로 routes/에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.rpa_result import RPAResult, RPAResultCreate, RPAResultUpdate

ENTITY_METAS: list[EntityMeta] = [
    EntityMeta(
        collection="rpa_results",
        prefix="RPAR",
        api_path="/api/v1/rpa/results",
        tag="RPA 결과",
        resource="rpa_result",
        model=RPAResult,
        create_schema=RPAResultCreate,
        update_schema=RPAResultUpdate,
        archetype="transaction",
        not_found_message="RPA 결과를 찾을 수 없습니다",
    ),
]
