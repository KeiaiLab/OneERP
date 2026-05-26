"""문서 관리 커스텀 라우터."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from oneerp_core.deps import CurrentUserDep
from oneerp_core.permissions import require_permission
from oneerp_core.repository import Repository

from ..models.document import DocumentCreate, DocumentUpdate
from ..services.category_service import CategoryService
from ..services.document_lifecycle_service import DocumentLifecycleService
from ..services.document_share_service import DocumentShareService
from ..services.document_signature_service import DocumentSignatureService
from ..services.retention_service import RetentionService

router = APIRouter(prefix="/api/v1/documents", tags=["문서관리"])

_RETENTION_WARNING_DAYS = 30


def _get_doc_repo(tenant_id: str) -> Repository:
    return Repository("documents", tenant_id=tenant_id)


def _get_category_repo(tenant_id: str) -> Repository:
    return Repository("document_categories", tenant_id=tenant_id)


def _get_share_repo(tenant_id: str) -> Repository:
    return Repository("document_shares", tenant_id=tenant_id)


def _get_signature_repo(tenant_id: str) -> Repository:
    return Repository("document_signatures", tenant_id=tenant_id)


def _get_version_repo(tenant_id: str) -> Repository:
    return Repository("document_versions", tenant_id=tenant_id)


def _get_audit_repo(tenant_id: str) -> Repository:
    return Repository("document_audit_logs", tenant_id=tenant_id)


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=UTC)
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
    return None


def _iso(value: Any) -> str | None:
    parsed = _as_datetime(value)
    return parsed.isoformat() if parsed else None


def _normalize_doc(document: dict[str, Any]) -> dict[str, Any]:
    return {
        **document,
        "id": document.get("_id", ""),
        "created_at": _iso(document.get("created_at")),
        "updated_at": _iso(document.get("updated_at")),
        "retention_until": _iso(document.get("retention_until")),
        "locked_at": _iso(document.get("locked_at")),
    }


def _status_badge(
    document: dict[str, Any],
    *,
    valid_signature_count: int,
    active_share_count: int,
    retention_due_soon: bool,
) -> str:
    status = document.get("status", "draft")
    if status == "draft" and document.get("is_locked"):
        return "draft_checked_out"
    if status == "draft":
        return "draft_editing"
    if status == "review":
        return "pending_review"
    if status == "approved":
        return "approved_ready_to_publish"
    if status == "published" and valid_signature_count > 0:
        return "published_signed"
    if status == "published" and active_share_count > 0:
        return "published_shared"
    if status == "published" and retention_due_soon:
        return "published_retention_due"
    if status == "published":
        return "published_active"
    if status == "archived":
        return "archived_retained"
    if status == "disposed":
        return "disposed"
    return status


def _recommended_action(
    document: dict[str, Any],
    *,
    valid_signature_count: int,
    external_link_count: int,
    retention_due_soon: bool,
) -> str:
    status = document.get("status", "draft")
    if status == "draft" and document.get("is_locked"):
        return "resolve_checkout"
    if status == "draft":
        return "submit_for_review"
    if status == "review":
        return "complete_review"
    if status == "approved":
        return "publish_document"
    if status == "published" and external_link_count > 0:
        return "review_external_shares"
    if status == "published" and valid_signature_count == 0:
        return "collect_signature"
    if status == "published" and retention_due_soon:
        return "review_retention_policy"
    if status == "archived":
        return "review_restore_or_dispose"
    if status == "disposed":
        return "review_disposal_log"
    return "review_document"


def _available_actions(
    document: dict[str, Any],
    *,
    valid_signature_count: int,
    active_share_count: int,
) -> list[str]:
    status = document.get("status", "draft")
    if status == "draft":
        return ["edit", "submit", "checkout"] if not document.get("is_locked") else ["checkin"]
    if status == "review":
        return ["approve", "reject", "open_audit_log"]
    if status == "approved":
        return ["publish", "open_versions", "open_audit_log"]
    if status == "published":
        actions = ["view_versions", "manage_shares", "archive"]
        if valid_signature_count > 0:
            actions.insert(2, "verify_signature")
        else:
            actions.insert(2, "sign")
        if active_share_count == 0:
            actions.append("share")
        return actions
    if status == "archived":
        return ["restore", "dispose", "open_audit_log"]
    return ["open_audit_log"]


def _decorate_document(
    document: dict[str, Any],
    *,
    categories: dict[str, dict[str, Any]],
    share_docs: list[dict[str, Any]],
    signature_docs: list[dict[str, Any]],
    version_docs: list[dict[str, Any]],
    audit_docs: list[dict[str, Any]],
) -> dict[str, Any]:
    doc_id = document.get("_id", "")
    shares = [
        share
        for share in share_docs
        if share.get("document_id") == doc_id and share.get("is_active", True)
    ]
    signatures = [
        signature
        for signature in signature_docs
        if signature.get("document_id") == doc_id and signature.get("is_valid", True)
    ]
    versions = [version for version in version_docs if version.get("document_id") == doc_id]
    audits = [audit for audit in audit_docs if audit.get("document_id") == doc_id]

    external_expiries = sorted(
        [
            parsed
            for share in shares
            if share.get("share_type") == "external_link"
            for parsed in [_as_datetime(share.get("expires_at"))]
            if parsed is not None
        ]
    )
    latest_external_expiry = external_expiries[-1] if external_expiries else None
    latest_signature = max(
        signatures,
        key=lambda item: _as_datetime(item.get("signed_at")) or datetime.min.replace(tzinfo=UTC),
        default=None,
    )
    latest_version = max(versions, key=lambda item: item.get("version_no", 0), default=None)
    latest_audit = max(
        audits,
        key=lambda item: _as_datetime(item.get("timestamp")) or datetime.min.replace(tzinfo=UTC),
        default=None,
    )

    retention_until = _as_datetime(document.get("retention_until"))
    retention_due_soon = bool(
        retention_until
        and retention_until <= datetime.now(tz=UTC) + timedelta(days=_RETENTION_WARNING_DAYS)
    )
    valid_signature_count = len(signatures)
    active_share_count = len(shares)
    external_link_count = sum(1 for share in shares if share.get("share_type") == "external_link")

    category = categories.get(document.get("category", ""))
    status_badge = _status_badge(
        document,
        valid_signature_count=valid_signature_count,
        active_share_count=active_share_count,
        retention_due_soon=retention_due_soon,
    )
    recommended_action = _recommended_action(
        document,
        valid_signature_count=valid_signature_count,
        external_link_count=external_link_count,
        retention_due_soon=retention_due_soon,
    )

    normalized = _normalize_doc(document)
    normalized["category_summary"] = {
        "id": document.get("category", ""),
        "name": category.get("name", "") if category else "",
    }
    normalized["status_badge"] = status_badge
    normalized["recommended_action"] = recommended_action
    normalized["available_actions"] = _available_actions(
        document,
        valid_signature_count=valid_signature_count,
        active_share_count=active_share_count,
    )
    normalized["share_summary"] = {
        "active_share_count": active_share_count,
        "external_link_count": external_link_count,
        "department_share_count": sum(
            1 for share in shares if share.get("share_type") == "department"
        ),
        "latest_external_expiry": _iso(latest_external_expiry),
    }
    normalized["signature_summary"] = {
        "valid_signature_count": valid_signature_count,
        "latest_signer": latest_signature.get("signer", "") if latest_signature else "",
        "last_signed_at": _iso(latest_signature.get("signed_at")) if latest_signature else None,
    }
    normalized["version_summary"] = {
        "current_version": document.get("version", 1),
        "total_versions": len(versions),
        "latest_change_summary": latest_version.get("change_summary", "") if latest_version else "",
    }
    normalized["audit_summary"] = {
        "event_count": len(audits),
        "last_action": latest_audit.get("action", "") if latest_audit else "",
        "last_actor": latest_audit.get("actor", "") if latest_audit else "",
    }
    normalized["retention_due_soon"] = retention_due_soon
    return normalized


def _load_workbench_documents(
    tenant_id: str,
    *,
    status: str | None = None,
    category: str | None = None,
    author: str | None = None,
    department: str | None = None,
    security_level: str | None = None,
    tags: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    repo = _get_doc_repo(tenant_id)
    docs = repo.find_many({}, limit=1000, sort=[("created_at", -1)])
    tag_terms = {term.strip().lower() for term in (tags or "").split(",") if term.strip()}
    keyword = (q or "").strip().lower()

    filtered: list[dict[str, Any]] = []
    for doc in docs:
        if doc.get("is_deleted"):
            continue
        if status and doc.get("status") != status:
            continue
        if category and doc.get("category") != category:
            continue
        if author and doc.get("author") != author:
            continue
        if department and doc.get("department") != department:
            continue
        if security_level and doc.get("security_level") != security_level:
            continue
        if tag_terms and not tag_terms.issubset({str(tag).lower() for tag in doc.get("tags", [])}):
            continue
        searchable = " ".join(
            [
                str(doc.get("title", "")),
                str(doc.get("summary", "")),
                str(doc.get("content_plain", "")),
                " ".join(str(tag) for tag in doc.get("tags", [])),
            ]
        ).lower()
        if keyword and keyword not in searchable:
            continue
        filtered.append(doc)
    return filtered


def _build_workbench_rows(tenant_id: str, documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    category_repo = _get_category_repo(tenant_id)
    share_repo = _get_share_repo(tenant_id)
    signature_repo = _get_signature_repo(tenant_id)
    version_repo = _get_version_repo(tenant_id)
    audit_repo = _get_audit_repo(tenant_id)

    categories = {
        category.get("_id", ""): category
        for category in category_repo.find_many({}, limit=500)
        if category.get("_id")
    }
    shares = share_repo.find_many({}, limit=2000)
    signatures = signature_repo.find_many({}, limit=2000)
    versions = version_repo.find_many({}, limit=2000)
    audits = audit_repo.find_many({}, limit=4000)

    return [
        _decorate_document(
            document,
            categories=categories,
            share_docs=shares,
            signature_docs=signatures,
            version_docs=versions,
            audit_docs=audits,
        )
        for document in documents
    ]


def _build_summary(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {
        "draft_count": sum(1 for row in rows if row.get("status") == "draft"),
        "review_count": sum(1 for row in rows if row.get("status") == "review"),
        "approved_count": sum(1 for row in rows if row.get("status") == "approved"),
        "published_count": sum(1 for row in rows if row.get("status") == "published"),
        "archived_count": sum(1 for row in rows if row.get("status") == "archived"),
        "disposed_count": sum(1 for row in rows if row.get("status") == "disposed"),
        "locked_count": sum(1 for row in rows if row.get("is_locked")),
        "shared_externally_count": sum(
            1 for row in rows if row.get("share_summary", {}).get("external_link_count", 0) > 0
        ),
        "signed_count": sum(
            1
            for row in rows
            if row.get("signature_summary", {}).get("valid_signature_count", 0) > 0
        ),
        "retention_due_soon_count": sum(1 for row in rows if row.get("retention_due_soon")),
    }


@router.post(
    "",
    status_code=201,
    dependencies=[Depends(require_permission("document:create"))],
)
def create_document(body: DocumentCreate, user: CurrentUserDep) -> dict[str, Any]:
    """문서를 생성한다."""
    category_repo = _get_category_repo(user.tenant_id)
    category = category_repo.find_by_id(body.category)
    if not category:
        raise HTTPException(status_code=400, detail="유효한 문서 분류를 선택하세요 [ERR-DOC-002]")

    security_level = body.security_level.value
    if security_level == "internal" and category.get("default_security_level"):
        security_level = str(category.get("default_security_level"))

    svc = DocumentLifecycleService(user.tenant_id)
    created = svc.create_document(
        title=body.title,
        category=body.category,
        content=body.content,
        template_id=body.template_id,
        template_variables=body.template_variables,
        security_level=security_level,
        tags=body.tags,
        metadata=body.metadata,
        department=body.department,
        company=body.company,
        summary=body.summary,
        author=user.sub,
    )
    normalized = _normalize_doc(created)
    normalized["id"] = created.get("_id", "")
    return normalized


@router.get(
    "",
    dependencies=[Depends(require_permission("document:read"))],
)
def list_documents(
    user: CurrentUserDep,
    page: int = 1,
    page_size: int = Query(default=20, le=100),
    status: str | None = None,
    category: str | None = None,
    author: str | None = None,
    department: str | None = None,
    security_level: str | None = None,
    tags: str | None = None,
    q: str | None = None,
) -> dict[str, Any]:
    """문서 워크벤치 목록을 조회한다."""
    docs = _load_workbench_documents(
        user.tenant_id,
        status=status,
        category=category,
        author=author,
        department=department,
        security_level=security_level,
        tags=tags,
        q=q,
    )
    rows = _build_workbench_rows(user.tenant_id, docs)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "data": rows[start:end],
        "total": len(rows),
        "page": page,
        "page_size": page_size,
        "summary": _build_summary(rows),
    }


@router.get(
    "/{document_id}",
    dependencies=[Depends(require_permission("document:read"))],
)
def get_document(document_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """문서 상세를 조회한다."""
    docs = _load_workbench_documents(user.tenant_id)
    doc = next((item for item in docs if item.get("_id") == document_id), None)
    if not doc:
        raise HTTPException(
            status_code=404, detail="요청하신 문서를 찾을 수 없습니다 [ERR-DOC-040]"
        )
    return _build_workbench_rows(user.tenant_id, [doc])[0]


@router.put(
    "/{document_id}",
    dependencies=[Depends(require_permission("document:write"))],
)
def update_document(document_id: str, body: DocumentUpdate, user: CurrentUserDep) -> dict[str, Any]:
    """문서를 수정한다."""
    if body.category:
        category = _get_category_repo(user.tenant_id).find_by_id(body.category)
        if not category:
            raise HTTPException(
                status_code=400, detail="유효한 문서 분류를 선택하세요 [ERR-DOC-002]"
            )

    svc = DocumentLifecycleService(user.tenant_id)
    updated = svc.update_document(document_id, actor=user.sub, **body.model_dump(exclude_none=True))
    normalized = _normalize_doc(updated)
    normalized["id"] = updated.get("_id", document_id)
    return normalized


@router.delete(
    "/{document_id}",
    status_code=204,
    dependencies=[Depends(require_permission("document:delete"))],
)
def delete_document(document_id: str, user: CurrentUserDep) -> Response:
    """문서를 소프트 삭제한다."""
    svc = DocumentLifecycleService(user.tenant_id)
    svc.soft_delete_document(document_id, actor=user.sub)
    return Response(status_code=204)


@router.get(
    "/{document_id}/summary",
    dependencies=[Depends(require_permission("document:read"))],
)
def get_document_summary(document_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """문서 상세 워크벤치 요약을 조회한다."""
    document = get_document(document_id, user)
    return {
        "id": document.get("id", document_id),
        "title": document.get("title", ""),
        "status_badge": document.get("status_badge", ""),
        "recommended_action": document.get("recommended_action", ""),
        "available_actions": document.get("available_actions", []),
        "lifecycle_summary": {
            "status": document.get("status", ""),
            "current_version": document.get("version", 1),
            "is_locked": document.get("is_locked", False),
            "locked_by": document.get("locked_by"),
            "retention_until": document.get("retention_until"),
        },
        "version_summary": document.get("version_summary", {}),
        "sharing_summary": document.get("share_summary", {}),
        "signature_summary": document.get("signature_summary", {}),
        "audit_summary": document.get("audit_summary", {}),
    }


@router.post(
    "/{document_id}/submit",
    dependencies=[Depends(require_permission("document:write"))],
)
def submit_document(document_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """문서를 제출한다 (draft → review)."""
    svc = DocumentLifecycleService(user.tenant_id)
    return svc.submit_document(document_id, actor=user.sub)


@router.post(
    "/{document_id}/approve",
    dependencies=[Depends(require_permission("document:write"))],
)
def approve_document(document_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """문서를 승인한다 (review → approved)."""
    svc = DocumentLifecycleService(user.tenant_id)
    return svc.approve_document(document_id, actor=user.sub)


@router.post(
    "/{document_id}/reject",
    dependencies=[Depends(require_permission("document:write"))],
)
def reject_document(
    document_id: str,
    user: CurrentUserDep,
    reason: str = "",
) -> dict[str, Any]:
    """문서를 반려한다 (review → draft)."""
    svc = DocumentLifecycleService(user.tenant_id)
    return svc.reject_document(document_id, actor=user.sub, reason=reason)


@router.post(
    "/{document_id}/publish",
    dependencies=[Depends(require_permission("document:write"))],
)
def publish_document(document_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """문서를 배포한다 (approved/draft → published)."""
    svc = DocumentLifecycleService(user.tenant_id)
    return svc.publish_document(document_id, actor=user.sub)


@router.post(
    "/{document_id}/archive",
    dependencies=[Depends(require_permission("document:write"))],
)
def archive_document(document_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """문서를 아카이브한다 (published/approved → archived)."""
    svc = DocumentLifecycleService(user.tenant_id)
    return svc.archive_document(document_id, actor=user.sub)


@router.post(
    "/{document_id}/restore",
    dependencies=[Depends(require_permission("document:write"))],
)
def restore_document(document_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """아카이브된 문서를 복원한다 (archived → published)."""
    svc = DocumentLifecycleService(user.tenant_id)
    return svc.restore_document(document_id, actor=user.sub)


@router.post(
    "/{document_id}/dispose",
    dependencies=[Depends(require_permission("document:delete"))],
)
def dispose_document(document_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """문서를 폐기한다 (published/archived → disposed)."""
    svc = DocumentLifecycleService(user.tenant_id)
    return svc.dispose_document(document_id, actor=user.sub)


@router.post(
    "/{document_id}/checkout",
    dependencies=[Depends(require_permission("document:write"))],
)
def checkout_document(document_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """문서를 체크아웃한다 (편집 잠금)."""
    svc = DocumentLifecycleService(user.tenant_id)
    return svc.checkout_document(document_id, actor=user.sub)


@router.post(
    "/{document_id}/checkin",
    dependencies=[Depends(require_permission("document:write"))],
)
def checkin_document(document_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """문서를 체크인한다 (잠금 해제)."""
    svc = DocumentLifecycleService(user.tenant_id)
    return svc.checkin_document(document_id, actor=user.sub)


@router.post(
    "/{document_id}/versions/{version_no}/restore",
    dependencies=[Depends(require_permission("document:write"))],
)
def restore_version(document_id: str, version_no: int, user: CurrentUserDep) -> dict[str, Any]:
    """특정 버전에서 문서를 복원한다."""
    svc = DocumentLifecycleService(user.tenant_id)
    return svc.restore_version(document_id, version_no, actor=user.sub)


@router.post(
    "/{document_id}/share",
    status_code=201,
    dependencies=[Depends(require_permission("document:write"))],
)
def share_document(
    document_id: str,
    body: dict[str, Any],
    user: CurrentUserDep,
) -> dict[str, Any]:
    """문서를 공유한다."""
    svc = DocumentShareService(user.tenant_id)
    expires_at = body.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    return svc.create_share(
        document_id=document_id,
        share_type=body.get("share_type", "user"),
        target_user=body.get("target_user"),
        target_department=body.get("target_department"),
        permission=body.get("permission", "viewer"),
        expires_at=expires_at,
        password=body.get("password"),
        max_downloads=body.get("max_downloads"),
        shared_by=user.sub,
    )


@router.get(
    "/{document_id}/shares",
    dependencies=[Depends(require_permission("document:read"))],
)
def list_document_shares(document_id: str, user: CurrentUserDep) -> list[dict[str, Any]]:
    """문서의 공유 목록을 조회한다."""
    svc = DocumentShareService(user.tenant_id)
    return svc.get_shares_by_document(document_id)


@router.post(
    "/{document_id}/sign",
    status_code=201,
    dependencies=[Depends(require_permission("document:write"))],
)
def sign_document(
    document_id: str,
    body: dict[str, Any],
    user: CurrentUserDep,
) -> dict[str, Any]:
    """문서에 전자서명을 수행한다."""
    svc = DocumentSignatureService(user.tenant_id)
    return svc.sign_document(
        document_id=document_id,
        signer=user.sub,
        signature_type=body.get("signature_type", "joint_certificate"),
        signature_data=body.get("signature_data", ""),
        certificate_info=body.get("certificate_info"),
        certificate_serial=body.get("certificate_serial"),
    )


@router.get(
    "/{document_id}/signatures",
    dependencies=[Depends(require_permission("document:read"))],
)
def list_document_signatures(document_id: str, user: CurrentUserDep) -> list[dict[str, Any]]:
    """문서의 서명 목록을 조회한다."""
    svc = DocumentSignatureService(user.tenant_id)
    return svc.get_signatures_by_document(document_id)


@router.delete(
    "/{document_id}/soft-delete",
    dependencies=[Depends(require_permission("document:delete"))],
)
def soft_delete_document(document_id: str, user: CurrentUserDep) -> dict[str, Any]:
    """문서를 소프트 삭제한다."""
    svc = DocumentLifecycleService(user.tenant_id)
    return svc.soft_delete_document(document_id, actor=user.sub)


@router.get(
    "/categories/tree",
    dependencies=[Depends(require_permission("document_category:read"))],
)
def get_category_tree(
    user: CurrentUserDep,
    root_id: str | None = None,
) -> list[dict[str, Any]]:
    """카테고리 트리를 조회한다."""
    svc = CategoryService(user.tenant_id)
    return svc.get_category_tree(root_id)


@router.get(
    "/retention/expired",
    dependencies=[Depends(require_permission("document:read"))],
)
def list_expired_documents(user: CurrentUserDep) -> list[dict[str, Any]]:
    """보존 기간이 만료된 문서를 조회한다."""
    svc = RetentionService(user.tenant_id)
    return svc.find_expired_documents()
