"""검사결과(InspectionResult) 라우트 단위 테스트 — Log 패턴."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_qm_app.quality.main import app

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


@patch("oneerp_qm_app.quality.routes.inspection_results._get_repo")
@patch(
    "oneerp_qm_app.quality.routes.inspection_results.generate_name", return_value="INSR-2026-00001"
)
def test_검사결과_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """필수 필드로 검사결과를 생성하면 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/inspection-results/",
        json={"inspection_id": "QI-001", "parameter": "경도"},
    )
    assert response.status_code == 201
    assert response.json()["inspection_result_id"] == "INSR-2026-00001"


@patch("oneerp_qm_app.quality.routes.inspection_results._get_repo")
def test_검사결과_목록_조회(mock_repo: MagicMock) -> None:
    """검사결과 목록을 조회하면 200과 페이지네이션 결과를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "INSR-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/inspection-results/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_qm_app.quality.routes.inspection_results._get_repo")
def test_검사결과_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 검사결과 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/inspection-results/NOT-EXIST")
    assert response.status_code == 404
