"""G3-1 AuthN · JWT nonce 재사용 거부 — scaffolding.

OIDC 흐름에서 동일 nonce 가 재발급되면 token replay 로 간주하여 거부.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.security
def test_동일_nonce_재사용_토큰은_401_거부(
    accounting_client: TestClient,
    protected_path: str,
    staging_available: bool,
) -> None:
    if not staging_available:
        pytest.skip("스테이징 인프라(Keycloak) 없음 — G3-1 스테이징 시 활성화")

    # 이전 요청에서 사용한 nonce 와 동일한 nonce 의 JWT
    reused_nonce_jwt = "eyJhbGciOiJIUzI1NiJ9.nonce_reused.sig"
    response = accounting_client.get(
        protected_path,
        headers={
            "Authorization": f"Bearer {reused_nonce_jwt}",
            "X-Tenant-ID": "tenant-demo",
        },
    )
    assert response.status_code == 401
