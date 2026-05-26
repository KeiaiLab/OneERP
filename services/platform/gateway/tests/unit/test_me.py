"""내 정보(Me) API 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from oneerp_gateway_app.routes.me import router

_app = FastAPI()
_app.include_router(router)
client = TestClient(_app)

# 인증 헤더 상수
TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


# ── Me 조회 ──


@patch("oneerp_gateway_app.services.me_service.Repository")
def test_me_조회_성공(mock_repo_cls: MagicMock) -> None:
    """인증된 사용자가 자신의 정보를 조회하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = []
    mock_repo_cls.return_value = repo

    response = client.get("/api/v1/me", headers=TENANT_ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["sub"] == "tenant-admin"
    assert data["tenant_id"] == "test-tenant"
    assert data["user_tier"] == "tenant_admin"
    assert "roles" in data
    assert "permissions" in data


@patch("oneerp_gateway_app.services.me_service.Repository")
def test_me_테넌트_정보_포함(mock_repo_cls: MagicMock) -> None:
    """테넌트 문서가 존재하면 tenant 정보와 enabled_modules를 포함한다."""
    repo = MagicMock()
    # 첫 호출: 테넌트 조회, 두 번째 호출: 사용자 조회
    tenant_doc = {
        "tenant_name": "테스트 회사",
        "plan": "standard",
        "is_active": True,
    }
    repo.find_many.side_effect = [[tenant_doc], []]
    mock_repo_cls.return_value = repo

    response = client.get("/api/v1/me", headers=TENANT_ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["tenant"] is not None
    assert data["tenant"]["tenant_name"] == "테스트 회사"
    assert "enabled_modules" in data


@patch("oneerp_gateway_app.services.me_service.Repository")
def test_me_레거시_테넌트_필드도_정상_해석(mock_repo_cls: MagicMock) -> None:
    """시드 데이터의 name/status/enabled_modules 형식도 tenant 응답으로 변환한다."""
    repo = MagicMock()
    tenant_doc = {
        "name": "기본 테넌트",
        "status": "active",
        "enabled_modules": ["selling", "accounting"],
    }
    repo.find_many.side_effect = [[tenant_doc], []]
    mock_repo_cls.return_value = repo

    response = client.get("/api/v1/me", headers=TENANT_ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["tenant"]["tenant_name"] == "기본 테넌트"
    assert data["tenant"]["is_active"] is True
    assert data["enabled_modules"] == ["accounting", "gateway", "selling"]


# ── Me 수정 ──


@patch("oneerp_gateway_app.services.me_service.Repository")
def test_me_수정_성공(mock_repo_cls: MagicMock) -> None:
    """인증된 사용자가 이메일을 수정하면 200을 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "USR-001", "username": "tenant-admin"}]
    mock_repo_cls.return_value = repo

    response = client.put(
        "/api/v1/me",
        json={"email": "new@test.com"},
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert "수정" in response.json()["message"]


@patch("oneerp_gateway_app.services.me_service.Repository")
def test_me_수정_허용_필드_외_무시(mock_repo_cls: MagicMock) -> None:
    """허용되지 않은 필드(예: roles)는 무시하고 수정할 내용 없음을 반환한다."""
    repo = MagicMock()
    mock_repo_cls.return_value = repo

    response = client.put(
        "/api/v1/me",
        json={"roles": ["admin", "superuser"]},
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert "없습니다" in response.json()["message"]


# ── 인증 없이 접근 ──


@patch("oneerp_gateway_app.services.me_service.Repository")
def test_me_무인증_요청_401(mock_repo_cls: MagicMock) -> None:
    """헤더 없는 요청은 debug 모드와 무관하게 401을 반환한다."""
    repo = MagicMock()
    repo.find_many.return_value = []
    mock_repo_cls.return_value = repo

    response = client.get("/api/v1/me")
    assert response.status_code == 401
