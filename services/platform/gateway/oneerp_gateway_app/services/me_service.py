"""현재 사용자 정보 조합 서비스."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from oneerp_core.modules import get_allowed_modules
from oneerp_core.repository import Repository

if TYPE_CHECKING:
    from oneerp_core.deps import CurrentUser


def get_me_payload(user: CurrentUser) -> dict[str, Any]:
    result: dict[str, Any] = {
        "sub": user.sub,
        "tenant_id": user.tenant_id,
        "roles": list(user.roles),
        "permissions": list(user.permissions),
        "user_tier": user.user_tier,
        "is_super_admin": user.is_super_admin,
    }

    tenant_repo = Repository("tenants", tenant_id=user.tenant_id)
    tenants = tenant_repo.find_many({"_id": user.tenant_id}, limit=1)
    if tenants:
        tenant = tenants[0]
        tenant_name = str(tenant.get("tenant_name") or tenant.get("name") or "")
        is_active = tenant.get("is_active")
        if is_active is None:
            is_active = tenant.get("status", "active") == "active"
        allowed_modules = tenant.get("allowed_modules") or tenant.get("enabled_modules") or []
        result["tenant"] = {
            "tenant_name": tenant_name,
            "plan": tenant.get("plan", "standard"),
            "is_active": is_active,
        }
        plan = tenant.get("plan", "standard")
        result["enabled_modules"] = sorted(get_allowed_modules(plan, allowed_modules or None))
    else:
        result["tenant"] = None
        result["enabled_modules"] = []

    user_repo = Repository("users", tenant_id=user.tenant_id)
    user_docs = user_repo.find_many({"username": user.sub}, limit=1)
    if user_docs:
        user_doc = user_docs[0]
        result["email"] = user_doc.get("email", "")
        result["full_name"] = user_doc.get("full_name", "")

    return result


def filter_me_update_fields(body: dict[str, Any]) -> dict[str, Any]:
    allowed_fields = {"email", "full_name"}
    return {k: v for k, v in body.items() if k in allowed_fields}


def update_me_payload(*, user: CurrentUser, body: dict[str, Any]) -> dict[str, str]:
    update_data = filter_me_update_fields(body)
    if not update_data:
        return {"message": "수정할 내용이 없습니다"}

    user_repo = Repository("users", tenant_id=user.tenant_id)
    user_docs = user_repo.find_many({"username": user.sub}, limit=1)
    if not user_docs:
        return {"message": "사용자를 찾을 수 없습니다"}

    user_repo.update_by_id(str(user_docs[0]["_id"]), update_data)
    return {"message": "내 정보가 수정되었습니다"}
