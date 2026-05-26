"""G3-1 AuthN · JWT 서명 위변조 거부 — scaffolding."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.security
def test_서명_위변조된_jwt_는_401_거부(
    accounting_client: TestClient,
    protected_path: str,
    staging_available: bool,
) -> None:
    if not staging_available:
        pytest.skip("스테이징 인프라(Keycloak) 없음 — G3-1 스테이징 시 활성화")

    # 올바른 header.payload + 위조된 signature
    tampered = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ0ZXN0In0.WRONG_SIGNATURE"
    response = accounting_client.get(
        protected_path,
        headers={
            "Authorization": f"Bearer {tampered}",
            "X-Tenant-ID": "tenant-demo",
        },
    )
    assert response.status_code == 401
