"""감가상각(DepreciationEntry) 라우트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

_AUTH = {
    "X-Tenant-Id": "T001",
    "X-User-Sub": "U001",
    "X-User-Roles": "admin",
    "X-User-Permissions": "*:*",
}


@patch("oneerp_assets_app.routes.depreciation_entries._get_repo")
@patch("oneerp_assets_app.routes.depreciation_entries.generate_name", return_value="DEP-2026-00001")
def test_감가상각_생성_정상(mock_name: MagicMock, mock_repo: MagicMock, test_client) -> None:
    """필수 필드로 감가상각 항목을 생성하면 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = test_client.post(
        "/api/v1/depreciation-entries",
        json={"asset_ref": "ASSET-001"},
        headers=_AUTH,
    )
    assert response.status_code == 201
    assert response.json()["id"] == "DEP-2026-00001"


@patch("oneerp_assets_app.routes.depreciation_entries._get_repo")
def test_감가상각_목록_조회(mock_repo: MagicMock, test_client) -> None:
    """감가상각 목록을 조회하면 200과 페이지네이션 결과를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "DEP-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = test_client.get("/api/v1/depreciation-entries?page=1&page_size=10", headers=_AUTH)
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_assets_app.routes.depreciation_entries._get_repo")
def test_감가상각_조회_미존재_404(mock_repo: MagicMock, test_client) -> None:
    """존재하지 않는 감가상각 항목 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = test_client.get("/api/v1/depreciation-entries/NOT-EXIST", headers=_AUTH)
    assert response.status_code == 404


@patch("oneerp_assets_app.routes.depreciation_entries._get_repo")
def test_감가상각_삭제_정상(mock_repo: MagicMock, test_client) -> None:
    """감가상각 항목을 삭제하면 204를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "DEP-001"}
    mock_repo.return_value = repo
    response = test_client.delete("/api/v1/depreciation-entries/DEP-001", headers=_AUTH)
    assert response.status_code == 204
    repo.delete_by_id.assert_called_once_with("DEP-001")
