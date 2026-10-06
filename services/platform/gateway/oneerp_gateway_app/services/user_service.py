"""사용자 CRUD 및 워크벤치 유스케이스 서비스."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from oneerp_core.errors import OneERPError
from oneerp_core.naming import generate_name
from oneerp_core.repository import Repository

from oneerp_gateway_app.models.user import User, UserAuthProvider, UserInvitationStatus
from oneerp_gateway_app.services.password_hasher import hash_password
from oneerp_gateway_app.services.user_presenter import (
    build_summary,
    decorate_user,
    status_badge_for,
)

if TYPE_CHECKING:
    from oneerp_gateway_app.dto import UserCreate, UserUpdate

_COLLECTION = "users"
_COMPANY_COLLECTION = "companies"
_PREFIX = "USR"


def _get_repo(tenant_id: str) -> Repository:
    return Repository(_COLLECTION, tenant_id=tenant_id)


def _get_company_repo(tenant_id: str) -> Repository:
    return Repository(_COMPANY_COLLECTION, tenant_id=tenant_id)


def normalize_auth_provider(provider: Any, oidc_subject: str) -> str:
    if provider:
        return str(provider)
    return UserAuthProvider.OIDC.value if oidc_subject else UserAuthProvider.PASSWORD.value


def derive_invitation_status(*, auth_provider: str, oidc_subject: str, last_login: Any) -> str:
    if auth_provider == UserAuthProvider.OIDC.value and oidc_subject:
        return UserInvitationStatus.LINKED.value
    if last_login:
        return UserInvitationStatus.ACCEPTED.value
    return UserInvitationStatus.PENDING.value


def matches_filters(
    document: dict[str, Any],
    *,
    active_only: bool,
    status_badge: str | None,
    company_id: str | None,
    auth_provider: str | None,
) -> bool:
    if active_only and not document.get("is_active", True):
        return False
    if company_id is not None and str(document.get("company_id") or "") != company_id:
        return False
    if auth_provider is not None and str(document.get("auth_provider") or "") != auth_provider:
        return False
    return not (status_badge is not None and status_badge_for(document) != status_badge)


def validate_company(company_repo: Repository, company_id: str) -> None:
    if company_id and not company_repo.find_by_id(company_id):
        raise OneERPError(
            status_code=422, error="validation_error", detail="소속 회사를 찾을 수 없습니다"
        )


def build_company_lookup(
    company_repo: Repository, documents: list[dict[str, Any]]
) -> dict[str, str]:
    company_ids = {
        str(document.get("company_id") or "")
        for document in documents
        if document.get("company_id")
    }
    lookup: dict[str, str] = {}
    for company_id in company_ids:
        company = company_repo.find_by_id(company_id)
        if company:
            lookup[company_id] = str(company.get("company_name") or "")
    return lookup


def prepare_user_payload(
    *,
    payload: dict[str, Any],
    actor_sub: str,
    company_repo: Repository,
    existing_document: dict[str, Any] | None = None,
    password: str | None = None,
) -> dict[str, Any]:
    existing_company_id = existing_document.get("company_id") if existing_document else ""
    company_id = str(
        payload.get("company_id") if payload.get("company_id") is not None else existing_company_id
    ).strip()
    if company_id:
        validate_company(company_repo, company_id)
    payload["company_id"] = company_id
    payload["department_name"] = str(
        payload.get("department_name")
        if payload.get("department_name") is not None
        else (existing_document.get("department_name") if existing_document else "")
    ).strip()
    oidc_subject = str(
        payload.get("oidc_subject")
        if payload.get("oidc_subject") is not None
        else (existing_document.get("oidc_subject") if existing_document else "")
    ).strip()
    auth_provider = normalize_auth_provider(payload.get("auth_provider"), oidc_subject)
    payload["auth_provider"] = auth_provider
    payload["oidc_subject"] = oidc_subject

    current_last_login = existing_document.get("last_login") if existing_document else None
    invitation_status = derive_invitation_status(
        auth_provider=auth_provider,
        oidc_subject=oidc_subject,
        last_login=current_last_login,
    )
    payload["invitation_status"] = invitation_status
    if invitation_status == UserInvitationStatus.PENDING.value:
        payload["invited_at"] = (
            existing_document.get("invited_at") if existing_document else datetime.now(UTC)
        )
        payload["invited_by"] = (
            existing_document.get("invited_by") if existing_document else actor_sub
        )
    elif invitation_status == UserInvitationStatus.LINKED.value:
        payload["invited_at"] = existing_document.get("invited_at") if existing_document else None
        payload["invited_by"] = (
            existing_document.get("invited_by") if existing_document else actor_sub
        )

    if password:
        payload["password_hash"] = hash_password(password)
    return payload


def get_user_or_404(repo: Repository, doc_id: str) -> dict[str, Any]:
    document = repo.find_by_id(doc_id)
    if not document:
        raise OneERPError(status_code=404, error="not_found", detail="사용자를 찾을 수 없습니다")
    return document


def create_user(*, tenant_id: str, actor_sub: str, body: UserCreate) -> dict[str, Any]:
    repo = _get_repo(tenant_id)
    company_repo = _get_company_repo(tenant_id)
    doc_id = generate_name(_PREFIX, tenant_id=tenant_id)
    raw_payload = body.model_dump(exclude={"password"})
    payload = prepare_user_payload(
        payload=raw_payload,
        actor_sub=actor_sub,
        company_repo=company_repo,
        password=body.password,
    )
    document = User(_id=doc_id, tenant_id=tenant_id, **payload)
    repo.insert(document)
    return {"user_id": doc_id, "id": doc_id, "message": "사용자가 생성되었습니다"}


def list_users(
    *,
    tenant_id: str,
    page: int,
    page_size: int,
    active_only: bool,
    status_badge: str | None,
    company_id: str | None,
    auth_provider: str | None,
) -> dict[str, Any]:
    repo = _get_repo(tenant_id)
    company_repo = _get_company_repo(tenant_id)
    documents = repo.find_many(limit=1000, sort=[("created_at", -1)])
    documents = [
        document
        for document in documents
        if matches_filters(
            document,
            active_only=active_only,
            status_badge=status_badge,
            company_id=company_id,
            auth_provider=auth_provider,
        )
    ]
    company_lookup = build_company_lookup(company_repo, documents)
    decorated = [decorate_user(document, company_lookup) for document in documents]
    skip = max(page - 1, 0) * page_size
    paged = decorated[skip : skip + page_size]
    return {
        "data": paged,
        "total": len(decorated),
        "page": page,
        "page_size": page_size,
        "summary": build_summary(documents),
    }


def get_user_summary(*, tenant_id: str, doc_id: str) -> dict[str, Any]:
    repo = _get_repo(tenant_id)
    company_repo = _get_company_repo(tenant_id)
    document = get_user_or_404(repo, doc_id)
    company_lookup = build_company_lookup(company_repo, [document])
    return decorate_user(document, company_lookup)


def get_user(*, tenant_id: str, doc_id: str) -> dict[str, Any]:
    return get_user_summary(tenant_id=tenant_id, doc_id=doc_id)


def update_user(*, tenant_id: str, actor_sub: str, doc_id: str, body: UserUpdate) -> dict[str, Any]:
    repo = _get_repo(tenant_id)
    company_repo = _get_company_repo(tenant_id)
    document = get_user_or_404(repo, doc_id)
    update_data = body.model_dump(exclude_none=True, exclude={"password"})
    update_data = prepare_user_payload(
        payload=update_data,
        actor_sub=actor_sub,
        company_repo=company_repo,
        existing_document=document,
        password=body.password,
    )
    repo.update_by_id(doc_id, update_data)
    return {"message": "사용자가 수정되었습니다"}


def delete_user(*, tenant_id: str, doc_id: str) -> None:
    repo = _get_repo(tenant_id)
    document = get_user_or_404(repo, doc_id)
    if document.get("is_active", True):
        raise OneERPError(
            status_code=422,
            error="validation_error",
            detail="활성 사용자는 삭제할 수 없습니다. 먼저 비활성화하세요",
        )
    repo.delete_by_id(doc_id)
