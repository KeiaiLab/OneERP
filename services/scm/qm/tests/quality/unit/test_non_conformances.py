"""부적합(NonConformance) 라우트 단위 테스트."""

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


@patch("oneerp_qm_app.quality.routes.non_conformances._get_repo")
@patch("oneerp_qm_app.quality.routes.non_conformances.generate_name", return_value="NC-2026-00001")
def test_부적합_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """필수 필드로 부적합을 생성하면 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/non-conformances/",
        json={"title": "표면 결함 발견"},
    )
    assert response.status_code == 201
    assert response.json()["non_conformance_id"] == "NC-2026-00001"


@patch("oneerp_qm_app.quality.routes.non_conformances._get_repo")
def test_부적합_목록_조회(mock_repo: MagicMock) -> None:
    """부적합 목록을 조회하면 200과 페이지네이션 결과를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "NC-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/non-conformances/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_qm_app.quality.routes.non_conformances._get_repo")
def test_부적합_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 부적합 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/non-conformances/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_qm_app.quality.routes.non_conformances._get_repo")
def test_부적합_제출_정상(mock_repo: MagicMock) -> None:
    """초안 상태의 부적합을 제출하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "NC-001", "docstatus": 0}
    mock_repo.return_value = repo
    response = client.post("/api/v1/non-conformances/NC-001/submit")
    assert response.status_code == 200
    repo.submit_with_event.assert_called_once()


@patch("oneerp_qm_app.quality.routes.non_conformances._get_repo")
def test_부적합_취소_정상(mock_repo: MagicMock) -> None:
    """제출된 부적합을 취소하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "NC-001", "docstatus": 1}
    mock_repo.return_value = repo
    response = client.post("/api/v1/non-conformances/NC-001/cancel")
    assert response.status_code == 200
    repo.cancel.assert_called_once_with("NC-001")
