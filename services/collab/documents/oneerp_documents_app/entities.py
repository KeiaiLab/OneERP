"""Documents 서비스 엔티티 메타 선언 — CRUD 라우터 자동 생성용.

8개 엔티티를 EntityMeta로 선언한다.
"""

from __future__ import annotations

from oneerp_core.entity_meta import EntityMeta

from .models.document import Document, DocumentCreate, DocumentUpdate
from .models.document_audit_log import (
    DocumentAuditLog,
    DocumentAuditLogCreate,
    DocumentAuditLogUpdate,
)
from .models.document_category import (
    DocumentCategory,
    DocumentCategoryCreate,
    DocumentCategoryUpdate,
)
from .models.document_share import DocumentShare, DocumentShareCreate, DocumentShareUpdate
from .models.document_signature import (
    DocumentSignature,
    DocumentSignatureCreate,
    DocumentSignatureUpdate,
)
from .models.document_template import (
    DocumentTemplate,
    DocumentTemplateCreate,
    DocumentTemplateUpdate,
)
from .models.document_version import (
    DocumentVersion,
    DocumentVersionCreate,
    DocumentVersionUpdate,
)
from .models.retention_policy import (
    RetentionPolicy,
    RetentionPolicyCreate,
    RetentionPolicyUpdate,
)

# --- 마스터 데이터 ---

DOCUMENT_CATEGORY = EntityMeta(
    collection="document_categories",
    prefix="DC",
    api_path="/api/v1/document-categories",
    tag="문서 분류",
    resource="document_category",
    model=DocumentCategory,
    create_schema=DocumentCategoryCreate,
    update_schema=DocumentCategoryUpdate,
    archetype="master",
    not_found_message="문서 분류를 찾을 수 없습니다",
)

RETENTION_POLICY = EntityMeta(
    collection="retention_policies",
    prefix="RP",
    api_path="/api/v1/retention-policies",
    tag="보존 정책",
    resource="retention_policy",
    model=RetentionPolicy,
    create_schema=RetentionPolicyCreate,
    update_schema=RetentionPolicyUpdate,
    archetype="master",
    not_found_message="보존 정책을 찾을 수 없습니다",
)

DOCUMENT_TEMPLATE = EntityMeta(
    collection="document_templates",
    prefix="DT",
    api_path="/api/v1/document-templates",
    tag="문서 템플릿",
    resource="document_template",
    model=DocumentTemplate,
    create_schema=DocumentTemplateCreate,
    update_schema=DocumentTemplateUpdate,
    archetype="master",
    not_found_message="문서 템플릿을 찾을 수 없습니다",
)

# --- 트랜잭션 문서 ---

DOCUMENT = EntityMeta(
    collection="documents",
    prefix="DOC",
    api_path="/api/v1/documents",
    tag="문서",
    resource="document",
    model=Document,
    create_schema=DocumentCreate,
    update_schema=DocumentUpdate,
    archetype="transaction",
    not_found_message="문서를 찾을 수 없습니다",
)

DOCUMENT_VERSION = EntityMeta(
    collection="document_versions",
    prefix="DV",
    api_path="/api/v1/document-versions",
    tag="문서 버전",
    resource="document_version",
    model=DocumentVersion,
    create_schema=DocumentVersionCreate,
    update_schema=DocumentVersionUpdate,
    archetype="transaction",
    not_found_message="문서 버전을 찾을 수 없습니다",
)

DOCUMENT_SHARE = EntityMeta(
    collection="document_shares",
    prefix="DS",
    api_path="/api/v1/document-shares",
    tag="문서 공유",
    resource="document_share",
    model=DocumentShare,
    create_schema=DocumentShareCreate,
    update_schema=DocumentShareUpdate,
    archetype="transaction",
    not_found_message="문서 공유를 찾을 수 없습니다",
)

DOCUMENT_SIGNATURE = EntityMeta(
    collection="document_signatures",
    prefix="SG",
    api_path="/api/v1/document-signatures",
    tag="전자서명",
    resource="document_signature",
    model=DocumentSignature,
    create_schema=DocumentSignatureCreate,
    update_schema=DocumentSignatureUpdate,
    archetype="transaction",
    not_found_message="전자서명을 찾을 수 없습니다",
)

DOCUMENT_AUDIT_LOG = EntityMeta(
    collection="document_audit_logs",
    prefix="AL",
    api_path="/api/v1/document-audit-logs",
    tag="문서 감사 로그",
    resource="document_audit_log",
    model=DocumentAuditLog,
    create_schema=DocumentAuditLogCreate,
    update_schema=DocumentAuditLogUpdate,
    archetype="transaction",
    not_found_message="감사 로그를 찾을 수 없습니다",
)

# 전체 엔티티 메타 목록
ENTITY_METAS = [
    # 마스터
    DOCUMENT_CATEGORY,
    RETENTION_POLICY,
    DOCUMENT_TEMPLATE,
    # 트랜잭션
    DOCUMENT_VERSION,
    DOCUMENT_SHARE,
    DOCUMENT_SIGNATURE,
    DOCUMENT_AUDIT_LOG,
]
