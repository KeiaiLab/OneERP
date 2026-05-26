"""품질목표(QualityGoal) 라우트 단위 테스트."""

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


@patch("oneerp_qm_app.quality.routes.quality_goals._get_repo")
@patch("oneerp_qm_app.quality.routes.quality_goals.generate_name", return_value="QGOL-2026-00001")
def test_품질목표_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """필수 필드로 품질목표를 생성하면 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/quality-goals/",
        json={"goal_name": "불량률 1% 이하"},
    )
    assert response.status_code == 201
    assert response.json()["quality_goal_id"] == "QGOL-2026-00001"


@patch("oneerp_qm_app.quality.routes.quality_goals._get_repo")
def test_품질목표_목록_조회(mock_repo: MagicMock) -> None:
    """품질목표 목록을 조회하면 200과 페이지네이션 결과를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "QGOL-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/quality-goals/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_qm_app.quality.routes.quality_goals._get_repo")
def test_품질목표_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 품질목표 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/quality-goals/NOT-EXIST")
    assert response.status_code == 404
