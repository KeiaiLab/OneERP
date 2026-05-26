"""G3-1 AuthN · JWT 만료 토큰 거부 — scaffolding.

스테이징(Keycloak·OPA) 미가동 시 `skip`. 활성화 시 401 기대.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.security
def test_만료된_jwt_는_401_거부(
    accounting_client: TestClient,
    protected_path: str,
    staging_available: bool,
) -> None:
    if not staging_available:
        pytest.skip("스테이징 인프라(Keycloak) 없음 — G3-1 스테이징 시 활성화")

    # exp 가 지난 토큰 — 스테이징에서 실제 발급 후 주입
    expired_jwt = "eyJhbGciOiJIUzI1NiJ9.expired.payload"
    response = accounting_client.get(
        protected_path,
        headers={
            "Authorization": f"Bearer {expired_jwt}",
            "X-Tenant-ID": "tenant-demo",
        },
    )
    assert response.status_code == 401, f"만료 JWT 는 401 이어야 함 · 실제={response.status_code}"
