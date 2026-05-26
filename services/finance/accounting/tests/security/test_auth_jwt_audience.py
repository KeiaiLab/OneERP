"""G3-1 AuthN · JWT audience 불일치 거부 — scaffolding."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.security
def test_audience_불일치_jwt_는_401_거부(
    accounting_client: TestClient,
    protected_path: str,
    staging_available: bool,
) -> None:
    if not staging_available:
        pytest.skip("스테이징 인프라(Keycloak) 없음 — G3-1 스테이징 시 활성화")

    # aud=other-app 인 토큰 — 스테이징에서 실제 발급
    wrong_aud_jwt = "eyJhbGciOiJIUzI1NiJ9.aud_mismatch.sig"
    response = accounting_client.get(
        protected_path,
        headers={
            "Authorization": f"Bearer {wrong_aud_jwt}",
            "X-Tenant-ID": "tenant-demo",
        },
    )
    assert response.status_code == 401
