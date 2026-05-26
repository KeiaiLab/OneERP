"""G3-1 AuthN · JWT replay(로그아웃/revoke 후 재사용) 거부 — scaffolding."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.security
def test_revoke된_jwt_재사용은_401_거부(
    accounting_client: TestClient,
    protected_path: str,
    staging_available: bool,
) -> None:
    if not staging_available:
        pytest.skip("스테이징 인프라(Keycloak·jti deny-list) 없음 — G3-1 스테이징 시 활성화")

    # 로그아웃으로 jti 가 revoke 된 후 재제출된 토큰
    revoked_jwt = "eyJhbGciOiJIUzI1NiJ9.revoked_jti.sig"
    response = accounting_client.get(
        protected_path,
        headers={
            "Authorization": f"Bearer {revoked_jwt}",
            "X-Tenant-ID": "tenant-demo",
        },
    )
    assert response.status_code == 401
