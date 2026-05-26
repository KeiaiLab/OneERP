"""E2E 인증 헬퍼 — 로그인으로 JWT를 획득하고, 로그아웃으로 세션을 종료한다.

세션 컨텍스트 매니저 형태로 제공해 로그인↔로그아웃 짝을 강제한다.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import httpx


class AuthSession:
    """로그인된 E2E 세션 — Bearer 토큰 + 테넌트 헤더를 자동 첨부한다."""

    def __init__(self, gateway_url: str, tenant_id: str, token: str) -> None:
        self._gateway_url = gateway_url.rstrip("/")
        self._tenant_id = tenant_id
        self._token = token

    @property
    def headers(self) -> dict[str, str]:
        """인증 요청에 필요한 공통 헤더."""
        return {
            "Authorization": f"Bearer {self._token}",
            "X-Tenant-Id": self._tenant_id,
        }

    def client(self, base_url: str, *, timeout: float = 10.0) -> httpx.Client:
        """주어진 서비스 base_url에 Bearer 토큰이 미리 설정된 httpx 클라이언트를 반환한다."""
        return httpx.Client(
            base_url=base_url,
            headers=self.headers,
            timeout=timeout,
        )


def login(gateway_url: str, *, tenant_id: str, username: str, password: str) -> str:
    """Gateway /auth/login 호출 → access_token 반환."""
    resp = httpx.post(
        f"{gateway_url.rstrip('/')}/api/v1/auth/login",
        json={"username": username, "password": password},
        headers={"X-Tenant-Id": tenant_id},
        timeout=10.0,
    )
    assert resp.status_code == 200, f"로그인 실패: {resp.status_code} {resp.text}"
    data: dict[str, Any] = resp.json()
    token = data.get("access_token")
    assert token, f"로그인 응답에 access_token 누락: {data}"
    return token


def logout(gateway_url: str, *, token: str, tenant_id: str) -> None:
    """Gateway /auth/logout 호출 — 쿠키 세션을 종료한다."""
    resp = httpx.post(
        f"{gateway_url.rstrip('/')}/api/v1/auth/logout",
        headers={
            "Authorization": f"Bearer {token}",
            "X-Tenant-Id": tenant_id,
        },
        timeout=10.0,
    )
    # 로그아웃은 유효하지 않은 토큰에서도 관대하게 처리
    assert resp.status_code in (200, 401), f"로그아웃 예상외 응답: {resp.status_code} {resp.text}"


@contextmanager
def auth_session(
    gateway_url: str,
    *,
    tenant_id: str,
    username: str,
    password: str,
) -> Iterator[AuthSession]:
    """로그인 → yield → 로그아웃을 보장하는 컨텍스트 매니저."""
    token = login(
        gateway_url,
        tenant_id=tenant_id,
        username=username,
        password=password,
    )
    try:
        yield AuthSession(gateway_url, tenant_id, token)
    finally:
        logout(gateway_url, token=token, tenant_id=tenant_id)
