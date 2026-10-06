"""E2E 테스트용 시드 데이터 — 테넌트/사용자/역할을 FerretDB에 직접 주입한다.

pytest 세션 시작 시 한 번 실행되어, 로그인 가능한 초기 상태를 보장한다.
로그인 플로우는 이 시드된 데이터를 전제로 동작한다.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from oneerp_gateway_app.services.password_hasher import hash_password
from pymongo import MongoClient

E2E_TENANT_ID = "default"
E2E_USERNAME = "e2e_admin"
E2E_PASSWORD = "e2e-pass-2026"  # noqa: S105


def seed_minimal_auth(client: MongoClient, db_name: str) -> dict[str, Any]:
    """로그인 가능한 최소 상태를 시드한다.

    반환값: {tenant_id, username, password, roles} — 로그인 플로우가 직접 사용.
    """
    db = client[db_name]
    now = datetime.now(tz=UTC)

    # 테넌트 — 기본 모듈 전체 허용
    db.tenants.update_one(
        {"_id": E2E_TENANT_ID},
        {
            "$set": {
                "_id": E2E_TENANT_ID,
                "tenant_id": E2E_TENANT_ID,
                "tenant_name": "E2E 테스트 테넌트",
                "plan": "enterprise",
                "enabled_modules": [
                    "selling",
                    "buying",
                    "stock",
                    "accounting",
                    "hr",
                    "payroll",
                ],
                "is_active": True,
                "created_at": now,
            },
        },
        upsert=True,
    )

    # 역할 권한 — admin 와일드카드로 단순화
    db.role_permissions.update_one(
        {"tenant_id": E2E_TENANT_ID, "role": "admin", "doctype": "*"},
        {
            "$set": {
                "tenant_id": E2E_TENANT_ID,
                "role": "admin",
                "doctype": "*",
                "read": True,
                "write": True,
                "create": True,
                "delete": True,
                "submit": True,
                "cancel": True,
            },
        },
        upsert=True,
    )

    # E2E 관리자 사용자
    db.users.update_one(
        {"tenant_id": E2E_TENANT_ID, "username": E2E_USERNAME},
        {
            "$set": {
                "tenant_id": E2E_TENANT_ID,
                "username": E2E_USERNAME,
                "email": "e2e@oneerp.test",
                "full_name": "E2E 관리자",
                "roles": ["admin"],
                "user_tier": "super_admin",
                "is_super_admin": True,
                "is_active": True,
                "auth_provider": "password",
                "password_hash": hash_password(E2E_PASSWORD),
                "created_at": now,
            },
        },
        upsert=True,
    )

    return {
        "tenant_id": E2E_TENANT_ID,
        "username": E2E_USERNAME,
        "password": E2E_PASSWORD,
        "roles": ["admin"],
    }
