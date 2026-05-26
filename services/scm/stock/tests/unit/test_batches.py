"""로트(Batch) CRUD 엔드포인트 테스트."""

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


@patch("oneerp_stock_app.routes.batches._get_repo")
@patch("oneerp_stock_app.routes.batches.generate_name", return_value="BATCH-2026-00001")
def test_로트_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/batches/ -- 정상 생성 시 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/batches/",
        json={
            "item_code": "ITEM-001",
            "manufacturing_date": "2026-03-17",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["batch_id"] == "BATCH-2026-00001"


@patch("oneerp_stock_app.routes.batches._get_repo")
def test_로트_목록_조회(mock_repo: MagicMock) -> None:
    """GET /api/v1/batches/ -- 페이지네이션 응답 구조를 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "BATCH-001", "item_code": "ITEM-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/batches/?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1


@patch("oneerp_stock_app.routes.batches._get_repo")
def test_로트_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/batches/{doc_id} -- 없는 로트는 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/batches/NOT-EXIST")
    assert response.status_code == 404
