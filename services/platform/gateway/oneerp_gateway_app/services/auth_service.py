"""인증 유스케이스 서비스."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

import jwt
from oneerp_core.config import get_core_settings
from oneerp_core.errors import raise_forbidden, raise_unauthorized
from oneerp_core.repository import Repository

from .password_hasher import hash_password, needs_rehash, verify_password
from .token_service import (
    clear_auth_cookies,
    create_access_token,
    create_refresh_token,
    decode_token,
    set_auth_cookies,
)

if TYPE_CHECKING:
    from fastapi import Request, Response


def _require_tenant_header(request: Request) -> str:
    """로그인 요청의 tenant 헤더를 검증한다. 없으면 기본 테넌트 사용."""
    tenant_id = request.headers.get("X-Tenant-Id", "").strip()
    if not tenant_id:
        tenant_id = get_core_settings().default_tenant
    return tenant_id


def login(*, username: str, password: str, request: Request, response: Response) -> dict[str, Any]:
    """로그인 유스케이스를 수행한다."""
    tenant_id = _require_tenant_header(request)
    repo = Repository("users", tenant_id=tenant_id)
    docs = repo.find_many({"username": username}, limit=1)
    if not docs:
        raise_unauthorized("사용자명 또는 비밀번호가 올바르지 않습니다")

    user_doc = docs[0]
    auth_provider = str(user_doc.get("auth_provider") or "password")
    if auth_provider == "oidc":
        raise_unauthorized("OIDC 연동 계정입니다. SSO 로그인을 사용하세요")

    stored_hash = user_doc.get("password_hash", "")
    if not stored_hash:
        raise_unauthorized("비밀번호가 아직 설정되지 않았습니다")
    if not verify_password(password, stored_hash):
        raise_unauthorized("사용자명 또는 비밀번호가 올바르지 않습니다")

    if not user_doc.get("is_active", True):
        raise_forbidden("비활성화된 계정입니다")

    access_token, expires_in = create_access_token(user_doc)
    refresh_token = create_refresh_token(username=username, tenant_id=tenant_id)
    set_auth_cookies(
        response,
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )

    # 레거시 해시는 로그인 성공 시 scrypt 로 교체한다.
    updates: dict[str, Any] = {"last_login": datetime.now(tz=UTC)}
    if needs_rehash(stored_hash):
        updates["password_hash"] = hash_password(password)
    if user_doc.get("_id"):
        repo.update_by_id(str(user_doc["_id"]), updates)

    return {"access_token": access_token, "expires_in": expires_in}


def refresh(*, request: Request, response: Response) -> dict[str, Any]:
    """리프레시 토큰으로 새 액세스 토큰을 발급한다."""
    token = request.cookies.get("refresh_token", "")
    if not token:
        raise_unauthorized("리프레시 토큰이 필요합니다")

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError:
        raise_unauthorized("리프레시 토큰이 만료되었습니다")
    except jwt.InvalidTokenError:
        raise_unauthorized("유효하지 않은 리프레시 토큰입니다")

    if payload.get("type") != "refresh":
        raise_unauthorized("유효하지 않은 리프레시 토큰입니다")

    tenant_id = str(payload.get("tenant_id", "")).strip()
    username = str(payload.get("sub", "")).strip()
    if not tenant_id or not username:
        raise_unauthorized("유효하지 않은 리프레시 토큰입니다")

    repo = Repository("users", tenant_id=tenant_id)
    docs = repo.find_many({"username": username}, limit=1)
    if not docs or not docs[0].get("is_active", True):
        raise_unauthorized("유효하지 않은 리프레시 토큰입니다")

    user_doc = docs[0]
    access_token, expires_in = create_access_token(user_doc)
    new_refresh_token = create_refresh_token(username=username, tenant_id=tenant_id)
    set_auth_cookies(
        response,
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=expires_in,
    )
    return {"access_token": access_token, "expires_in": expires_in}


def logout(*, response: Response) -> dict[str, str]:
    """로그아웃 — 쿠키 삭제."""
    clear_auth_cookies(response)
    return {"message": "로그아웃되었습니다"}
