"""Knowledge 서비스 엔티티 메타 선언 — FAQ/분류 CRUD 자동 생성용.

지식 문서는 버전 비교/리뷰 주기 등 커스텀 라우트가 필요해 routes/에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.faq import Faq, FaqCreate, FaqUpdate
from .models.knowledge_category import (
    KnowledgeCategory,
    KnowledgeCategoryCreate,
    KnowledgeCategoryUpdate,
)

# --- 마스터 데이터 ---

KNOWLEDGE_CATEGORY = EntityMeta(
    collection="knowledge_categories",
    prefix="KC",
    api_path="/api/v1/knowledge-categories",
    tag="지식 분류",
    resource="knowledge_category",
    model=KnowledgeCategory,
    create_schema=KnowledgeCategoryCreate,
    update_schema=KnowledgeCategoryUpdate,
    archetype="master",
    not_found_message="지식 분류를 찾을 수 없습니다",
)

FAQ = EntityMeta(
    collection="faqs",
    prefix="FAQ",
    api_path="/api/v1/faqs",
    tag="FAQ",
    resource="faq",
    model=Faq,
    create_schema=FaqCreate,
    update_schema=FaqUpdate,
    archetype="transaction",
    not_found_message="FAQ를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    KNOWLEDGE_CATEGORY,
    FAQ,
]
