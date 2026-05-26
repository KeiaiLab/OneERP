"""품질검사(QualityInspection) 라우트 단위 테스트."""

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


@patch("oneerp_qm_app.quality.routes.quality_inspections._get_repo")
@patch(
    "oneerp_qm_app.quality.routes.quality_inspections.generate_name",
    return_value="QI-2026-00001",
)
def test_품질검사_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """필수 필드로 품질검사를 생성하면 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/quality-inspections",
        json={
            "reference_type": "purchase_receipt",
            "reference_no": "PR-001",
            "inspection_type": "incoming",
            "item_code": "ITEM-001",
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "QI-2026-00001"


@patch("oneerp_qm_app.quality.routes.quality_inspections._get_repo")
def test_품질검사_목록_조회(mock_repo: MagicMock) -> None:
    """품질검사 목록을 조회하면 200과 페이지네이션 결과를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "QI-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/quality-inspections?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_qm_app.quality.routes.quality_inspections._get_repo")
def test_품질검사_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 품질검사 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/quality-inspections/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_qm_app.quality.routes.quality_inspections._get_repo")
def test_품질검사_제출_정상(mock_repo: MagicMock) -> None:
    """초안 상태의 품질검사를 제출하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "QI-001", "docstatus": 0}
    mock_repo.return_value = repo
    response = client.post("/api/v1/quality-inspections/QI-001/submit")
    assert response.status_code == 200
    repo.submit_with_event.assert_called_once()


@patch("oneerp_qm_app.quality.routes.quality_inspections._get_repo")
def test_품질검사_삭제_정상(mock_repo: MagicMock) -> None:
    """품질검사를 삭제하면 204를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "QI-001", "docstatus": 0}
    mock_repo.return_value = repo
    response = client.delete("/api/v1/quality-inspections/QI-001")
    assert response.status_code == 204
    repo.delete_by_id.assert_called_once_with("QI-001")
