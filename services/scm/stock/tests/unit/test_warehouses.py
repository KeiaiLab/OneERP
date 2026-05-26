"""창고(Warehouse) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_stock_app.main import app

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


@patch("oneerp_stock_app.routes.warehouses._get_repo")
@patch("oneerp_stock_app.routes.warehouses.generate_name", return_value="WH-2026-00001")
def test_창고_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/warehouses/",
        json={"warehouse_name": "본사 창고", "warehouse_type": "stores"},
    )
    assert response.status_code == 201
    assert response.json()["warehouse_id"] == "WH-2026-00001"


@patch("oneerp_stock_app.routes.warehouses._get_repo")
def test_창고_목록_조회(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "WH-001", "warehouse_name": "창고A"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/warehouses/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_stock_app.routes.warehouses._get_repo")
def test_창고_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/warehouses/NOT-EXIST")
    assert response.status_code == 404
