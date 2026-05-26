"""서비스 레지스트리 엔드포인트 테스트."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi.testclient import TestClient


def test_서비스_목록_조회(test_client: TestClient) -> None:
    """등록된 서비스 목록이 반환되는지 검증한다."""
    response = test_client.get("/api/v1/services")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert data["total"] >= 3

    names = [s["name"] for s in data["data"]]
    assert "selling" in names
    assert "stock" in names
    assert "accounting" in names

    # 각 항목에 필수 필드가 있는지 확인
    for service in data["data"]:
        assert "name" in service
        assert "url" in service
        assert "health_url" in service
        assert "status" in service
