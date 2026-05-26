"""이슈(Issue) API 엔드포인트 테스트."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

if TYPE_CHECKING:
    from types import ModuleType

    from fastapi.testclient import TestClient


def test_이슈_생성(test_client: TestClient, issues_mod: ModuleType) -> None:
    """이슈 생성 API가 정상 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.insert.return_value = "ISS-2026-00001"

    with (
        patch.object(issues_mod, "_get_repo", return_value=mock_repo),
        patch("oneerp_crm_app.routes.issues.generate_name", return_value="ISS-2026-00001"),
    ):
        response = test_client.post(
            "/api/v1/issues",
            json={
                "subject": "로그인 오류",
                "description": "비밀번호 입력 후 무한 로딩",
                "customer_id": "CUST-001",
                "priority": "high",
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "ISS-2026-00001"


def test_이슈_목록_조회(test_client: TestClient, issues_mod: ModuleType) -> None:
    """이슈 목록 API가 정상 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_many.return_value = [{"_id": "ISS-2026-00001", "subject": "로그인 오류"}]
    mock_repo.count.return_value = 1

    with patch.object(issues_mod, "_get_repo", return_value=mock_repo):
        response = test_client.get("/api/v1/issues")

    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_이슈_해결(test_client: TestClient, issues_mod: ModuleType) -> None:
    """이슈 해결 API가 정상 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "ISS-2026-00001", "status": "open"}
    mock_repo.update_by_id.return_value = True

    with patch.object(issues_mod, "_get_repo", return_value=mock_repo):
        response = test_client.post(
            "/api/v1/issues/ISS-2026-00001/resolve",
            json={
                "resolution": "비밀번호 재설정 링크 전송",
            },
        )

    assert response.status_code == 200
    assert "해결" in response.json()["message"]


def test_이슈_종료(test_client: TestClient, issues_mod: ModuleType) -> None:
    """이슈 종료 API가 정상 동작하는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "ISS-2026-00001", "status": "resolved"}
    mock_repo.update_by_id.return_value = True

    with patch.object(issues_mod, "_get_repo", return_value=mock_repo):
        response = test_client.post("/api/v1/issues/ISS-2026-00001/close")

    assert response.status_code == 200
    assert "종료" in response.json()["message"]


def test_미해결_이슈_종료_거부(test_client: TestClient, issues_mod: ModuleType) -> None:
    """resolved가 아닌 이슈의 종료가 거부되는지 검증한다 (BR-CRM-010)."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "ISS-2026-00001", "status": "open"}

    with patch.object(issues_mod, "_get_repo", return_value=mock_repo):
        response = test_client.post("/api/v1/issues/ISS-2026-00001/close")

    assert response.status_code == 422


def test_진행중_이슈_종료_거부(test_client: TestClient, issues_mod: ModuleType) -> None:
    """in_progress 상태 이슈의 종료가 거부되는지 검증한다 (BR-CRM-010)."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "ISS-2026-00001", "status": "in_progress"}

    with patch.object(issues_mod, "_get_repo", return_value=mock_repo):
        response = test_client.post("/api/v1/issues/ISS-2026-00001/close")

    assert response.status_code == 422


def test_이미_종료된_이슈_종료_거부(test_client: TestClient, issues_mod: ModuleType) -> None:
    """이미 종료된 이슈의 재종료가 거부되는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "ISS-2026-00001", "status": "closed"}

    with patch.object(issues_mod, "_get_repo", return_value=mock_repo):
        response = test_client.post("/api/v1/issues/ISS-2026-00001/close")

    assert response.status_code == 400


def test_해결된_이슈_수정_거부(test_client: TestClient, issues_mod: ModuleType) -> None:
    """해결된 이슈의 수정이 거부되는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "ISS-2026-00001", "status": "resolved"}

    with patch.object(issues_mod, "_get_repo", return_value=mock_repo):
        response = test_client.put(
            "/api/v1/issues/ISS-2026-00001",
            json={
                "subject": "수정된 제목",
            },
        )

    assert response.status_code == 400


def test_이슈_삭제_open만_허용(test_client: TestClient, issues_mod: ModuleType) -> None:
    """open 상태가 아닌 이슈의 삭제가 거부되는지 검증한다."""
    mock_repo = MagicMock()
    mock_repo.find_by_id.return_value = {"_id": "ISS-2026-00001", "status": "in_progress"}

    with patch.object(issues_mod, "_get_repo", return_value=mock_repo):
        response = test_client.delete("/api/v1/issues/ISS-2026-00001")

    assert response.status_code == 400
