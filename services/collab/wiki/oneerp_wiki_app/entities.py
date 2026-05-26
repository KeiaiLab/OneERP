"""위키 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

6개 엔티티를 EntityMeta로 선언한다.
커스텀 로직이 있는 위키 페이지(publish/archive)는
routes/ 디렉토리에서 직접 관리한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.wiki_attachment import (
    WikiAttachment,
    WikiAttachmentCreate,
    WikiAttachmentUpdate,
)
from .models.wiki_comment import WikiComment, WikiCommentCreate, WikiCommentUpdate
from .models.wiki_page import WikiPage, WikiPageCreate, WikiPageUpdate
from .models.wiki_page_revision import (
    WikiPageRevision,
    WikiPageRevisionCreate,
    WikiPageRevisionUpdate,
)
from .models.wiki_space import WikiSpace, WikiSpaceCreate, WikiSpaceUpdate
from .models.wiki_template import WikiTemplate, WikiTemplateCreate, WikiTemplateUpdate

# --- 마스터 데이터 ---

WIKI_SPACE = EntityMeta(
    collection="wiki_spaces",
    prefix="WS",
    api_path="/api/v1/wiki-spaces",
    tag="위키공간",
    resource="wiki_space",
    model=WikiSpace,
    create_schema=WikiSpaceCreate,
    update_schema=WikiSpaceUpdate,
    archetype="master",
    not_found_message="위키 공간을 찾을 수 없습니다",
)

WIKI_TEMPLATE = EntityMeta(
    collection="wiki_templates",
    prefix="WT",
    api_path="/api/v1/wiki-templates",
    tag="위키템플릿",
    resource="wiki_template",
    model=WikiTemplate,
    create_schema=WikiTemplateCreate,
    update_schema=WikiTemplateUpdate,
    archetype="master",
    not_found_message="위키 템플릿을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

WIKI_PAGE = EntityMeta(
    collection="wiki_pages",
    prefix="WP",
    api_path="/api/v1/wiki-pages",
    tag="위키페이지",
    resource="wiki_page",
    model=WikiPage,
    create_schema=WikiPageCreate,
    update_schema=WikiPageUpdate,
    archetype="transaction",
    not_found_message="위키 페이지를 찾을 수 없습니다",
)

WIKI_PAGE_REVISION = EntityMeta(
    collection="wiki_page_revisions",
    prefix="WPR",
    api_path="/api/v1/wiki-page-revisions",
    tag="위키페이지리비전",
    resource="wiki_page_revision",
    model=WikiPageRevision,
    create_schema=WikiPageRevisionCreate,
    update_schema=WikiPageRevisionUpdate,
    archetype="transaction",
    not_found_message="위키 페이지 리비전을 찾을 수 없습니다",
)

WIKI_COMMENT = EntityMeta(
    collection="wiki_comments",
    prefix="WC",
    api_path="/api/v1/wiki-comments",
    tag="위키댓글",
    resource="wiki_comment",
    model=WikiComment,
    create_schema=WikiCommentCreate,
    update_schema=WikiCommentUpdate,
    archetype="transaction",
    not_found_message="위키 댓글을 찾을 수 없습니다",
)

WIKI_ATTACHMENT = EntityMeta(
    collection="wiki_attachments",
    prefix="WA",
    api_path="/api/v1/wiki-attachments",
    tag="위키첨부파일",
    resource="wiki_attachment",
    model=WikiAttachment,
    create_schema=WikiAttachmentCreate,
    update_schema=WikiAttachmentUpdate,
    archetype="transaction",
    not_found_message="위키 첨부파일을 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    WIKI_SPACE,
    WIKI_TEMPLATE,
    # 트랜잭션
    WIKI_PAGE,
    WIKI_PAGE_REVISION,
    WIKI_COMMENT,
    WIKI_ATTACHMENT,
]
