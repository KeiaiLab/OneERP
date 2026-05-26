"""JWT 토큰/쿠키 관련 서비스."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import jwt
from oneerp_core.config import get_core_settings

from .permission_service import resolve_permissions

if TYPE_CHECKING:
    from fastapi import Response


def _with_issuer_audience(payload: dict[str, Any]) -> dict[str, Any]:
    """설정된 issuer/audience claim을 JWT payload에 추가한다."""
    settings = get_core_settings()
    if settings.jwt_issuer:
        payload["iss"] = settings.jwt_issuer
    if settings.jwt_audience:
        payload["aud"] = settings.jwt_audience
    return payload


def create_refresh_token_payload(*, username: str, tenant_id: str) -> dict[str, Any]:
    """리프레시 토큰 payload를 생성한다."""
    settings = get_core_settings()
    expire = datetime.now(tz=UTC) + timedelta(days=settings.jwt_refresh_expiry_days)
    return _with_issuer_audience(
        {
            "sub": username,
            "tenant_id": tenant_id,
            "type": "refresh",
            "exp": expire,
            "iat": datetime.now(tz=UTC),
        }
    )


def create_access_token(user_doc: dict[str, Any]) -> tuple[str, int]:
    """사용자 문서로부터 JWT 액세스 토큰을 생성한다."""
    settings = get_core_settings()
    expires_delta = timedelta(minutes=settings.jwt_expiry_minutes)
    expire = datetime.now(tz=UTC) + expires_delta

    roles = user_doc.get("roles", [])
    if user_doc.get("role"):
        roles = [*roles, user_doc["role"]]
    permissions = resolve_permissions(roles, user_doc.get("tenant_id", ""))

    payload = _with_issuer_audience(
        {
            "sub": user_doc.get("username", ""),
            "tenant_id": user_doc.get("tenant_id", ""),
            "roles": roles,
            "permissions": permissions,
            "user_tier": user_doc.get("user_tier", "regular"),
            "is_super_admin": user_doc.get("is_super_admin", False),
            "exp": expire,
            "iat": datetime.now(tz=UTC),
        }
    )
    token = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")
    return token, int(expires_delta.total_seconds())


def create_refresh_token(*, username: str, tenant_id: str) -> str:
    """리프레시 토큰을 생성한다."""
    settings = get_core_settings()
    return jwt.encode(
        create_refresh_token_payload(username=username, tenant_id=tenant_id),
        settings.jwt_secret,
        algorithm="HS256",
    )


def decode_token(token: str) -> dict[str, Any]:
    """JWT 토큰을 디코드한다."""
    settings = get_core_settings()
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=["HS256"],
        audience=settings.jwt_audience or None,
        issuer=settings.jwt_issuer or None,
        options={
            "verify_aud": bool(settings.jwt_audience),
            "verify_iss": bool(settings.jwt_issuer),
        },
    )


def set_auth_cookies(
    response: Response,
    *,
    access_token: str,
    refresh_token: str,
    expires_in: int,
) -> None:
    """인증 쿠키를 응답에 기록한다."""
    response.set_cookie(
        key="token",
        value=access_token,
        httponly=True,
        samesite="lax",
        max_age=expires_in,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
    )


def clear_auth_cookies(response: Response) -> None:
    """인증 쿠키를 제거한다."""
    response.delete_cookie("token")
    response.delete_cookie("refresh_token")
