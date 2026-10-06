"""auth_service 직접 단위 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import jwt
import pytest
from fastapi import Request, Response
from oneerp_core.config import get_core_settings
from oneerp_core.errors import OneERPError
from oneerp_gateway_app.services.auth_service import login, refresh
from oneerp_gateway_app.services.password_hasher import verify_password
from oneerp_gateway_app.services.token_service import create_access_token


def _request_with_headers(
    headers: dict[str, str] | None = None, cookies: dict[str, str] | None = None
) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
    }
    request = Request(scope)
    if cookies:
        request._cookies = cookies  # type: ignore[attr-defined]
    return request


@patch("oneerp_gateway_app.services.permission_service.Repository")
@patch("oneerp_gateway_app.services.auth_service.Repository")
def test_login은_기본테넌트로_액세스토큰을_발급한다(
    mock_repo_cls: MagicMock,
    mock_permission_repo_cls: MagicMock,
) -> None:
    plain_password = "secret"  # noqa: S105
    user_repo = MagicMock()
    user_repo.find_many.return_value = [
        {
            "_id": "USR-001",
            "username": "demo",
            "tenant_id": "default",
            "roles": ["admin"],
            "password_hash": "2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b",
            "is_active": True,
        }
    ]
    mock_repo_cls.return_value = user_repo
    permission_repo = MagicMock()
    permission_repo.find_many.return_value = []
    mock_permission_repo_cls.return_value = permission_repo

    response = Response()
    result = login(
        username="demo",
        password=plain_password,
        request=_request_with_headers(),
        response=response,
    )

    assert result["access_token"]
    assert result["expires_in"] > 0
    user_repo.find_many.assert_called_once_with({"username": "demo"}, limit=1)


@patch("oneerp_gateway_app.services.permission_service.Repository")
def test_access_token은_설정된_issuer_audience를_포함한다(
    mock_permission_repo_cls: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ONEERP_JWT_ISSUER", "http://localhost:8080/realms/oneerp")
    monkeypatch.setenv("ONEERP_JWT_AUDIENCE", "oneerp-web")
    get_core_settings.cache_clear()
    try:
        permission_repo = MagicMock()
        permission_repo.find_many.return_value = []
        mock_permission_repo_cls.return_value = permission_repo

        token, _ = create_access_token(
            {
                "username": "demo",
                "tenant_id": "tenant-a",
                "roles": ["operator"],
            }
        )

        settings = get_core_settings()
        claims = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=["HS256"],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
        )
        assert claims["iss"] == settings.jwt_issuer
        assert claims["aud"] == settings.jwt_audience
    finally:
        monkeypatch.delenv("ONEERP_JWT_ISSUER", raising=False)
        monkeypatch.delenv("ONEERP_JWT_AUDIENCE", raising=False)
        get_core_settings.cache_clear()


@patch("oneerp_gateway_app.services.auth_service.decode_token")
def test_refresh는_type이_refresh가_아니면_거부한다(mock_decode_token: MagicMock) -> None:
    mock_decode_token.return_value = {"type": "access", "sub": "demo", "tenant_id": "default"}

    with pytest.raises(OneERPError) as exc_info:
        refresh(
            request=_request_with_headers(cookies={"refresh_token": "bad-token"}),
            response=Response(),
        )

    assert exc_info.value.status_code == 401
    assert "유효하지 않은 리프레시 토큰" in str(exc_info.value.detail)


@patch("oneerp_gateway_app.services.permission_service.Repository")
@patch("oneerp_gateway_app.services.auth_service.Repository")
def test_login은_레거시_해시를_scrypt로_교체한다(
    mock_repo_cls: MagicMock,
    mock_permission_repo_cls: MagicMock,
) -> None:
    user_repo = MagicMock()
    user_repo.find_many.return_value = [
        {
            "_id": "USR-001",
            "username": "demo",
            "tenant_id": "default",
            "roles": ["admin"],
            "password_hash": "2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b",
            "is_active": True,
        }
    ]
    mock_repo_cls.return_value = user_repo
    mock_permission_repo_cls.return_value.find_many.return_value = []

    login(
        username="demo",
        password="secret",  # noqa: S106
        request=_request_with_headers(),
        response=Response(),
    )

    updates = user_repo.update_by_id.call_args.args[1]
    assert updates["password_hash"].startswith("scrypt$")
    assert verify_password("secret", updates["password_hash"])
