"""헬스체크 엔드포인트 테스트."""

from __future__ import annotations

from fastapi.testclient import TestClient
from oneerp_gateway_app.main import app

client = TestClient(app)


def test_health_정상_응답() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data
    assert "version" in data
