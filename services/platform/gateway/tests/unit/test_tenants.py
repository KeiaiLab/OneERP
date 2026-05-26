"""테넌트(Tenant) 라우트 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.tenants import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)

# Super Admin 헤더 — tenants 라우트는 require_super_admin() 의존성 사용
SUPER_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "admin-user",
    "X-User-Roles": "admin",
    "X-User-Tier": "super_admin",
    "X-User-Permissions": "*:*",
}


@patch("oneerp_gateway_app.routes.tenants._get_repo")
@patch("oneerp_gateway_app.routes.tenants.generate_name", return_value="TNT-2026-00001")
def test_테넌트_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """필수 필드로 테넌트를 생성하면 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/tenants/",
        json={"tenant_name": "테스트 회사"},
        headers=SUPER_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["tenant_id"] == "TNT-2026-00001"


@patch("oneerp_gateway_app.routes.tenants._get_repo")
def test_테넌트_목록_조회(mock_repo: MagicMock) -> None:
    """테넌트 목록을 조회하면 200과 페이지네이션 결과를 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "TNT-001"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/tenants/?page=1&page_size=10",
        headers=SUPER_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


@patch("oneerp_gateway_app.routes.tenants._get_repo")
def test_테넌트_조회_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 테넌트 조회 시 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/tenants/NOT-EXIST",
        headers=SUPER_ADMIN_HEADERS,
    )
    assert response.status_code == 404
