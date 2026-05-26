"""역할 기반 권한 계산 서비스."""

from __future__ import annotations

from oneerp_core.repository import Repository


def resolve_permissions(roles: list[str], tenant_id: str) -> list[str]:
    """역할 목록에서 모든 권한을 수집한다."""
    if not roles:
        return []

    repo = Repository("role_permissions", tenant_id=tenant_id)
    permissions: list[str] = []
    for role_name in roles:
        docs = repo.find_many({"role": role_name}, limit=500)
        for doc in docs:
            doctype = doc.get("doctype", "")
            permissions.extend(
                f"{doctype}:{action}"
                for action in ("read", "write", "create", "delete", "submit", "cancel")
                if doc.get(action)
            )

    if "admin" in roles:
        permissions.append("*:*")
    return list(set(permissions))
