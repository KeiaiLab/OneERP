"""시스템설정(SystemSettings) 라우트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.system_settings import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)

# 인증 헤더 — system_settings 라우트는 CurrentUserDep 사용
TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


@patch("oneerp_gateway_app.routes.system_settings._get_repo")
@patch("oneerp_gateway_app.routes.system_settings.generate_name", return_value="SYSS-2026-00001")
def test_시스템설정_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """필수 필드로 시스템설정을 생성하면 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/system-settings/",
        json={"setting_key": "default_currency"},
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["system_settings_id"] == "SYSS-2026-00001"


@patch("oneerp_gateway_app.routes.system_settings._get_repo")
def test_시스템설정_목록_조회(mock_repo: MagicMock) -> None:
    """시스템설정 목록을 조회하면 200과 페이지네이션 결과를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "SYSS-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/system-settings/?page=1&page_size=10",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_gateway_app.routes.system_settings._get_repo")
def test_시스템설정_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 시스템설정 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/system-settings/NOT-EXIST",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 404
