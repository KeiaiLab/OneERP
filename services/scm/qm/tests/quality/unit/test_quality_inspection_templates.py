"""품질검사템플릿(QualityInspectionTemplate) 라우트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

_AUTH = {
    "X-Tenant-Id": "T001",
    "X-User-Sub": "U001",
    "X-User-Roles": "admin",
    "X-User-Permissions": "*:*",
}


@patch("oneerp_qm_app.quality.routes.quality_inspection_templates._get_repo")
@patch(
    "oneerp_qm_app.quality.routes.quality_inspection_templates.generate_name",
    return_value="QITM-2026-00001",
)
def test_품질검사템플릿_생성_정상(mock_name: MagicMock, mock_repo: MagicMock, test_client) -> None:
    """필수 필드로 품질검사템플릿을 생성하면 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = test_client.post(
        "/api/v1/quality-inspection-templates/",
        json={"template_name": "입고검사 기본"},
        headers=_AUTH,
    )
    assert response.status_code == 201
    assert response.json()["quality_inspection_template_id"] == "QITM-2026-00001"


@patch("oneerp_qm_app.quality.routes.quality_inspection_templates._get_repo")
def test_품질검사템플릿_목록_조회(mock_repo: MagicMock, test_client) -> None:
    """품질검사템플릿 목록을 조회하면 200과 페이지네이션 결과를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "QITM-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = test_client.get(
        "/api/v1/quality-inspection-templates/?page=1&page_size=10", headers=_AUTH
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_qm_app.quality.routes.quality_inspection_templates._get_repo")
def test_품질검사템플릿_조회_미존재_404(mock_repo: MagicMock, test_client) -> None:
    """존재하지 않는 품질검사템플릿 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = test_client.get("/api/v1/quality-inspection-templates/NOT-EXIST", headers=_AUTH)
    assert response.status_code == 404
