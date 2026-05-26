"""자산이동(AssetMovement) 라우트 단위 테스트."""

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


@patch("oneerp_assets_app.routes.asset_movements._get_repo")
@patch("oneerp_assets_app.routes.asset_movements.generate_name", return_value="AMOV-2026-00001")
def test_자산이동_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """필수 필드로 자산이동을 생성하면 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/asset-movements/",
        json={"asset": "ASSET-001", "to_location": "서울 본사"},
    )
    assert response.status_code == 201
    assert response.json()["asset_movement_id"] == "AMOV-2026-00001"


@patch("oneerp_assets_app.routes.asset_movements._get_repo")
def test_자산이동_목록_조회(mock_repo: MagicMock) -> None:
    """자산이동 목록을 조회하면 200과 페이지네이션 결과를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "AMOV-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/asset-movements/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_assets_app.routes.asset_movements._get_repo")
def test_자산이동_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 자산이동 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/asset-movements/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_assets_app.routes.asset_movements._get_repo")
def test_자산이동_제출_정상(mock_repo: MagicMock) -> None:
    """초안 상태의 자산이동을 제출하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "AMOV-001", "docstatus": 0}
    mock_repo.return_value = repo
    response = client.post("/api/v1/asset-movements/AMOV-001/submit")
    assert response.status_code == 200
    repo.submit_with_event.assert_called_once()


@patch("oneerp_assets_app.routes.asset_movements._get_repo")
def test_자산이동_취소_정상(mock_repo: MagicMock) -> None:
    """제출된 자산이동을 취소하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "AMOV-001", "docstatus": 1}
    mock_repo.return_value = repo
    response = client.post("/api/v1/asset-movements/AMOV-001/cancel")
    assert response.status_code == 200
    repo.cancel.assert_called_once_with("AMOV-001")
