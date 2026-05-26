"""인증(Auth) 라우트 테스트."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import jwt


def test_login_테넌트_헤더_없으면_기본테넌트_사용(test_client) -> None:
    """tenant 헤더 없는 로그인은 기본 테넌트로 조회 후 미존재 시 401을 반환한다."""
    response = test_client.post(
        "/api/v1/auth/login",
        json={"username": "tenant-admin", "password": "secret"},
    )

    # 기본 테넌트의 DB에서 사용자를 찾지 못하면 401
    assert response.status_code == 401


@patch("oneerp_gateway_app.services.permission_service.Repository")
@patch("oneerp_gateway_app.services.auth_service.Repository")
def test_login_테넌트별_사용자_조회(
    mock_repo_cls: MagicMock, mock_permission_repo_cls: MagicMock, test_client
) -> None:
    """로그인은 tenant 헤더 기준으로 users 컬렉션을 조회한다."""
    user_doc = {
        "_id": "USR-001",
        "username": "tenant-admin",
        "tenant_id": "tenant-a",
        "roles": ["admin"],
        "is_active": True,
        "password_hash": "2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b",
    }
    repos: list[tuple[str, str | None, MagicMock]] = []

    def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
        repo = MagicMock()
        repos.append((collection_name, tenant_id, repo))
        repo.find_many.return_value = [user_doc]
        return repo

    mock_repo_cls.side_effect = _repo_factory
    mock_permission_repo = MagicMock()
    mock_permission_repo.find_many.return_value = []
    mock_permission_repo_cls.return_value = mock_permission_repo

    response = test_client.post(
        "/api/v1/auth/login",
        json={"username": "tenant-admin", "password": "secret"},
        headers={"X-Tenant-Id": "tenant-a"},
    )

    assert response.status_code == 200
    assert any(name == "users" and tenant_id == "tenant-a" for name, tenant_id, _ in repos)


@patch("oneerp_gateway_app.services.auth_service.Repository")
def test_login_OIDC_연동계정은_패스워드로그인을_거부한다(
    mock_repo_cls: MagicMock, test_client
) -> None:
    """OIDC 연동 사용자는 패스워드 로그인 대신 SSO를 사용해야 한다."""
    user_doc = {
        "_id": "USR-001",
        "username": "oidc-user",
        "tenant_id": "tenant-a",
        "roles": ["admin"],
        "is_active": True,
        "auth_provider": "oidc",
        "oidc_subject": "oidc|123",
    }

    def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
        repo = MagicMock()
        if collection_name == "users":
            repo.find_many.return_value = [user_doc]
        else:
            repo.find_many.return_value = []
        return repo

    mock_repo_cls.side_effect = _repo_factory

    response = test_client.post(
        "/api/v1/auth/login",
        json={"username": "oidc-user", "password": "secret"},
        headers={"X-Tenant-Id": "tenant-a"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "OIDC 연동 계정입니다. SSO 로그인을 사용하세요"


@patch("oneerp_gateway_app.services.permission_service.Repository")
@patch("oneerp_gateway_app.services.auth_service.Repository")
def test_refresh_쿠키_성공(
    mock_repo_cls: MagicMock, mock_permission_repo_cls: MagicMock, test_client
) -> None:
    """유효한 refresh cookie는 새 토큰을 발급한다."""
    from oneerp_core.config import get_core_settings

    settings = get_core_settings()
    refresh_token = jwt.encode(
        {
            "sub": "tenant-admin",
            "tenant_id": "tenant-a",
            "type": "refresh",
            "exp": datetime.now(tz=UTC) + timedelta(days=7),
            "iat": datetime.now(tz=UTC),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    user_doc = {
        "_id": "USR-001",
        "username": "tenant-admin",
        "tenant_id": "tenant-a",
        "roles": ["admin"],
        "is_active": True,
    }

    def _repo_factory(collection_name: str, tenant_id: str | None = None) -> MagicMock:
        repo = MagicMock()
        repo.find_many.return_value = [user_doc]
        return repo

    mock_repo_cls.side_effect = _repo_factory
    mock_permission_repo = MagicMock()
    mock_permission_repo.find_many.return_value = []
    mock_permission_repo_cls.return_value = mock_permission_repo

    response = test_client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"  # noqa: S105
    assert "token=" in response.headers["set-cookie"]


def test_refresh_쿠키_없으면_401(test_client) -> None:
    """refresh cookie가 없으면 401을 반환한다."""
    response = test_client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
