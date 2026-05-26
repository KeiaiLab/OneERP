"""테넌트 관리 API (suspend/activate) 단위 테스트."""

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


@patch("oneerp_gateway_app.routes.tenants.clear_tenant_cache")
@patch("oneerp_gateway_app.routes.tenants._get_repo")
def test_테넌트_정지_성공(mock_repo: MagicMock, mock_cache: MagicMock) -> None:
    """테넌트를 정지하면 suspended_at, suspended_reason이 설정된다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "TNT-001", "is_active": True}
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/tenants/TNT-001/suspend",
        json={"reason": "미납으로 인한 정지"},
        headers=SUPER_ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "테넌트가 정지되었습니다"

    # update_by_id 호출 인자 확인
    call_args = repo.update_by_id.call_args
    assert call_args[0][0] == "TNT-001"
    update_dict = call_args[0][1]
    assert update_dict["suspended_reason"] == "미납으로 인한 정지"
    assert update_dict["suspended_at"] is not None
    assert update_dict["is_active"] is False

    # 캐시 무효화 호출 확인
    mock_cache.assert_called_once()


@patch("oneerp_gateway_app.routes.tenants._get_repo")
def test_테넌트_정지_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 테넌트를 정지하면 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/tenants/NOT-EXIST/suspend",
        json={"reason": "테스트"},
        headers=SUPER_ADMIN_HEADERS,
    )

    assert response.status_code == 404


@patch("oneerp_gateway_app.routes.tenants.clear_tenant_cache")
@patch("oneerp_gateway_app.routes.tenants._get_repo")
def test_테넌트_활성화_성공(mock_repo: MagicMock, mock_cache: MagicMock) -> None:
    """정지된 테넌트를 활성화하면 suspended_at=None, is_active=True로 복원된다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "TNT-001",
        "is_active": False,
        "suspended_at": "2026-03-20T00:00:00Z",
        "suspended_reason": "미납",
    }
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/tenants/TNT-001/activate",
        headers=SUPER_ADMIN_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["message"] == "테넌트가 활성화되었습니다"

    # update_by_id 호출 인자 확인
    call_args = repo.update_by_id.call_args
    assert call_args[0][0] == "TNT-001"
    update_dict = call_args[0][1]
    assert update_dict["suspended_at"] is None
    assert update_dict["suspended_reason"] == ""
    assert update_dict["is_active"] is True

    # 캐시 무효화 호출 확인
    mock_cache.assert_called_once()


@patch("oneerp_gateway_app.routes.tenants._get_repo")
def test_테넌트_활성화_미존재_404(mock_repo: MagicMock) -> None:
    """존재하지 않는 테넌트를 활성화하면 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo

    response = client.post(
        "/api/v1/tenants/NOT-EXIST/activate",
        headers=SUPER_ADMIN_HEADERS,
    )

    assert response.status_code == 404
