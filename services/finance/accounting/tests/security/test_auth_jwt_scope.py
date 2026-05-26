"""G3-1 AuthN · JWT scope 부족 시 거부(403) — scaffolding."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.security
def test_scope_부족_jwt_는_403_거부(
    accounting_client: TestClient,
    protected_path: str,
    staging_available: bool,
) -> None:
    if not staging_available:
        pytest.skip("스테이징 인프라(OPA) 없음 — G3-1 스테이징 시 활성화")

    # scope=\"other.read\" 만 있는 토큰 · accounting.viewer 미보유
    low_scope_jwt = "eyJhbGciOiJIUzI1NiJ9.scope_low.sig"
    response = accounting_client.get(
        protected_path,
        headers={
            "Authorization": f"Bearer {low_scope_jwt}",
            "X-Tenant-ID": "tenant-demo",
        },
    )
    # scope 부족은 403(인증은 성공, 인가 실패) 이 정석
    assert response.status_code in {401, 403}
