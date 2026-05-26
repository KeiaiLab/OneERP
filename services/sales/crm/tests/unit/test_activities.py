"""활동(Activity) API 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_crm_app.routes.activities import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)


@patch("oneerp_crm_app.routes.activities._get_repo")
@patch("oneerp_crm_app.routes.activities.generate_name", return_value="ACTV-2026-00001")
def test_활동_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """활동 생성 API가 정상 동작하는지 검증한다."""
    mock_repo.return_value = MagicMock()
    response = client.post("/api/v1/activities/", json={"activity_type": "전화"})
    assert response.status_code == 201
    assert response.json()["activity_id"] == "ACTV-2026-00001"


@patch("oneerp_crm_app.routes.activities._get_repo")
def test_활동_목록_조회(mock_repo: MagicMock) -> None:
    """활동 목록 API가 페이지네이션과 함께 동작하는지 검증한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "ACTV-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/activities/?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_crm_app.routes.activities._get_repo")
def test_활동_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 활동 조회 시 404를 반환하는지 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/activities/NOT-EXIST")
    assert response.status_code == 404
