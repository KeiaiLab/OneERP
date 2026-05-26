"""자산(Asset) 라우트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_assets_app.main import app

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


@patch("oneerp_assets_app.routes.assets._get_repo")
@patch("oneerp_assets_app.routes.assets.generate_name", return_value="ASSET-2026-00001")
def test_자산_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """필수 필드로 자산을 생성하면 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/assets",
        json={"asset_name": "노트북 A"},
    )
    assert response.status_code == 201
    assert response.json()["id"] == "ASSET-2026-00001"


@patch("oneerp_assets_app.routes.assets._get_repo")
def test_자산_목록_조회(mock_repo: MagicMock) -> None:
    """자산 목록을 조회하면 200과 페이지네이션 결과를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "ASSET-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/assets?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_assets_app.routes.assets._get_repo")
def test_자산_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 자산 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/assets/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_assets_app.routes.assets._get_repo")
def test_자산_제출_정상(mock_repo: MagicMock) -> None:
    """draft 상태의 자산을 제출하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "ASSET-001", "status": "draft"}
    mock_repo.return_value = repo
    response = client.post("/api/v1/assets/ASSET-001/submit")
    assert response.status_code == 200
    repo.submit_with_event.assert_called_once()


@patch("oneerp_assets_app.routes.assets._get_repo")
def test_자산_폐기_정상(mock_repo: MagicMock) -> None:
    """submitted 상태의 자산을 폐기하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "ASSET-001", "status": "submitted"}
    mock_repo.return_value = repo
    response = client.post("/api/v1/assets/ASSET-001/scrap")
    assert response.status_code == 200


@patch("oneerp_assets_app.routes.assets._get_repo")
def test_자산_삭제_draft만_허용(mock_repo: MagicMock) -> None:
    """submitted 상태의 자산 삭제 시 400을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "ASSET-001", "status": "submitted"}
    mock_repo.return_value = repo
    response = client.delete("/api/v1/assets/ASSET-001")
    assert response.status_code == 400
