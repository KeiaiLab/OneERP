"""CLM 헬스체크 엔드포인트 테스트."""

from __future__ import annotations

from fastapi.testclient import TestClient
from oneerp_compliance_app.clm.main import app

client = TestClient(app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)


def test_health_정상_응답() -> None:
    """GET /health — 정상 응답을 확인한다."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data
