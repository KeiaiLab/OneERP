"""사용자 워크벤치 응답 프레젠터."""

from __future__ import annotations

from collections import Counter
from datetime import datetime
from typing import Any

from oneerp_gateway_app.models.user import UserAuthProvider, UserInvitationStatus, UserTier


def stringify_datetime(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def is_admin_user(document: dict[str, Any]) -> bool:
    roles = list(document.get("roles", []) or [])
    if document.get("role"):
        roles.append(document["role"])
    return (
        document.get("user_tier") in {UserTier.SUPER_ADMIN.value, UserTier.TENANT_ADMIN.value}
        or bool(document.get("is_super_admin"))
        or "admin" in roles
    )


def status_badge_for(document: dict[str, Any]) -> str:
    if not document.get("is_active", True):
        return "inactive_user"
    auth_provider = str(document.get("auth_provider") or UserAuthProvider.PASSWORD.value)
    invitation_status = str(document.get("invitation_status") or UserInvitationStatus.NONE.value)
    oidc_subject = str(document.get("oidc_subject") or "")
    if auth_provider == UserAuthProvider.OIDC.value and oidc_subject:
        return "oidc_linked"
    if (
        auth_provider == UserAuthProvider.OIDC.value
        and invitation_status == UserInvitationStatus.PENDING.value
    ):
        return "oidc_pending"
    if invitation_status == UserInvitationStatus.PENDING.value:
        return "invited_pending"
    if is_admin_user(document):
        return "admin_user"
    return "active_user"


def recommended_action_for(document: dict[str, Any]) -> str:
    if not document.get("is_active", True):
        return "reactivate_user"
    auth_provider = str(document.get("auth_provider") or UserAuthProvider.PASSWORD.value)
    oidc_subject = str(document.get("oidc_subject") or "")
    invitation_status = str(document.get("invitation_status") or UserInvitationStatus.NONE.value)
    if auth_provider == UserAuthProvider.OIDC.value and not oidc_subject:
        return "complete_oidc_link"
    if invitation_status == UserInvitationStatus.PENDING.value:
        return "resend_invitation"
    if is_admin_user(document):
        return "review_access_scope"
    return "review_last_login"


def available_actions_for(document: dict[str, Any]) -> list[str]:
    actions = ["edit", "open_roles"]
    if is_admin_user(document):
        actions.append("review_access_scope")
    if document.get("is_active", True):
        actions.append("deactivate")
    else:
        actions.extend(["reactivate", "delete"])
    if str(document.get("invitation_status") or "") == UserInvitationStatus.PENDING.value:
        actions.append("resend_invitation")
    if str(document.get("auth_provider") or "") == UserAuthProvider.OIDC.value and not document.get(
        "oidc_subject"
    ):
        actions.append("link_oidc_identity")
    return actions


def access_summary_for(document: dict[str, Any], company_lookup: dict[str, str]) -> dict[str, Any]:
    roles = list(document.get("roles", []) or [])
    primary_role = roles[0] if roles else document.get("role", "")
    company_id = str(document.get("company_id") or "")
    return {
        "primary_role": primary_role,
        "role_count": len(roles) or (1 if document.get("role") else 0),
        "company_id": company_id,
        "company_name": company_lookup.get(company_id, ""),
        "department_name": str(document.get("department_name") or ""),
        "user_tier": str(document.get("user_tier") or UserTier.REGULAR.value),
        "is_super_admin": bool(document.get("is_super_admin", False)),
    }


def auth_summary_for(document: dict[str, Any]) -> dict[str, Any]:
    return {
        "auth_provider": str(document.get("auth_provider") or UserAuthProvider.PASSWORD.value),
        "oidc_subject": str(document.get("oidc_subject") or ""),
        "invitation_status": str(
            document.get("invitation_status") or UserInvitationStatus.NONE.value
        ),
        "last_login": stringify_datetime(document.get("last_login")),
    }


def decorate_user(document: dict[str, Any], company_lookup: dict[str, str]) -> dict[str, Any]:
    public = dict(document)
    if "_id" in public:
        public["id"] = public["_id"]
    public["status_badge"] = status_badge_for(public)
    public["recommended_action"] = recommended_action_for(public)
    public["available_actions"] = available_actions_for(public)
    public["access_summary"] = access_summary_for(public, company_lookup)
    public["auth_summary"] = auth_summary_for(public)
    public["invited_at"] = stringify_datetime(public.get("invited_at"))
    public["last_login"] = stringify_datetime(public.get("last_login"))
    return public


def build_summary(documents: list[dict[str, Any]]) -> dict[str, int]:
    status_counter = Counter(status_badge_for(document) for document in documents)
    return {
        "total_user_count": len(documents),
        "active_user_count": sum(1 for document in documents if document.get("is_active", True)),
        "inactive_user_count": sum(
            1 for document in documents if not document.get("is_active", True)
        ),
        "invited_user_count": sum(
            1
            for document in documents
            if str(document.get("invitation_status") or "") == UserInvitationStatus.PENDING.value
        ),
        "oidc_linked_count": status_counter.get("oidc_linked", 0),
        "admin_user_count": sum(1 for document in documents if is_admin_user(document)),
    }
