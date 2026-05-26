"""Super Admin API 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_core.errors import OneERPError, oneerp_error_handler
from oneerp_gateway_app.routes.admin import router

_app = FastAPI()
_app.add_exception_handler(OneERPError, oneerp_error_handler)  # type: ignore[arg-type]
_app.include_router(router)
client = TestClient(_app)

# 인증 헤더 상수
SUPER_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "admin-user",
    "X-User-Roles": "admin",
    "X-User-Tier": "super_admin",
    "X-User-Permissions": "*:*",
}

TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}

REGULAR_USER_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "regular-user",
    "X-User-Roles": "user",
    "X-User-Tier": "regular",
    "X-User-Permissions": "user:read",
}


# ── 테넌트 생성 ──


@patch("oneerp_gateway_app.routes.admin._get_tenant_repo")
@patch("oneerp_gateway_app.routes.admin.generate_name", return_value="TNT-2026-00001")
def test_테넌트_생성_super_admin_성공(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """Super Admin이 테넌트를 생성하면 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/admin/tenants",
        json={"tenant_name": "테스트 회사"},
        headers=SUPER_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    assert response.json()["tenant_id"] == "TNT-2026-00001"


# ── 테넌트 목록 ──


@patch("oneerp_gateway_app.routes.admin._get_tenant_repo")
def test_테넌트_목록_super_admin_성공(mock_repo: MagicMock) -> None:
    """Super Admin이 테넌트 목록을 조회하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "TNT-001", "tenant_name": "A사"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get(
        "/api/v1/admin/tenants?page=1&page_size=10",
        headers=SUPER_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["total"] == 1


# ── 권한 부족 테스트 ──


@patch("oneerp_gateway_app.routes.admin._get_tenant_repo")
def test_테넌트_생성_일반사용자_403(mock_repo: MagicMock) -> None:
    """일반 사용자가 테넌트를 생성하면 403을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/admin/tenants",
        json={"tenant_name": "테스트 회사"},
        headers=REGULAR_USER_HEADERS,
    )
    assert response.status_code == 403


@patch("oneerp_gateway_app.routes.admin._get_tenant_repo")
def test_테넌트_생성_tenant_admin_403(mock_repo: MagicMock) -> None:
    """Tenant Admin이 Super Admin 전용 라우트에 접근하면 403을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        "/api/v1/admin/tenants",
        json={"tenant_name": "테스트 회사"},
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 403


# ── 테넌트 정지/활성화 ──


@patch("oneerp_gateway_app.routes.admin._get_tenant_repo")
def test_테넌트_정지_super_admin_성공(mock_repo: MagicMock) -> None:
    """Super Admin이 테넌트를 정지하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "TNT-001", "is_active": True}
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/admin/tenants/TNT-001/suspend",
        headers=SUPER_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert "정지" in response.json()["message"]


@patch("oneerp_gateway_app.routes.admin._get_tenant_repo")
def test_테넌트_활성화_super_admin_성공(mock_repo: MagicMock) -> None:
    """Super Admin이 테넌트를 활성화하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "TNT-001", "is_active": False}
    mock_repo.return_value = repo
    response = client.post(
        "/api/v1/admin/tenants/TNT-001/activate",
        headers=SUPER_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert "활성화" in response.json()["message"]


# ── 모듈 설정 ──


@patch("oneerp_gateway_app.routes.admin._get_tenant_repo")
def test_모듈_설정_super_admin_성공(mock_repo: MagicMock) -> None:
    """Super Admin이 모듈 설정을 변경하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "TNT-001"}
    mock_repo.return_value = repo
    response = client.put(
        "/api/v1/admin/tenants/TNT-001/modules",
        json={"allowed_modules": ["selling", "buying", "stock"]},
        headers=SUPER_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert "모듈" in response.json()["message"]


# ── 플랫폼 통계 ──


@patch("oneerp_gateway_app.routes.admin.Repository")
@patch("oneerp_gateway_app.routes.admin._get_tenant_repo")
def test_플랫폼_통계_super_admin_성공(
    mock_tenant_repo: MagicMock, mock_repo_cls: MagicMock
) -> None:
    """Super Admin이 플랫폼 통계를 조회하면 200을 반환한다."""
    tenant_repo = MagicMock()
    tenant_repo.count.return_value = 5
    mock_tenant_repo.return_value = tenant_repo

    user_repo = MagicMock()
    user_repo.count.return_value = 100
    mock_repo_cls.return_value = user_repo

    response = client.get(
        "/api/v1/admin/stats",
        headers=SUPER_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_tenants" in data
    assert "total_users" in data
    assert "plan_distribution" in data
