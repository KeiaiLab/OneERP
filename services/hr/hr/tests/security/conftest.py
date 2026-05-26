"""hr 보안 테스트 공통 fixture.

unit/conftest.py 와 동일한 테스트 클라이언트를 재사용하되, 보안 시나리오 전용
페이로드(만료 JWT · 위조 서명 등) 헬퍼를 제공한다.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import jwt
import pytest
from oneerp_core.testing import clear_settings_cache, make_service_test_client

# hr 서비스 루트 — services/hr/hr
_SERVICE_ROOT = Path(__file__).resolve().parents[2]

# 테스트용 JWT 시크릿 — CoreSettings 기본 dev 시크릿 회피 (32bytes 이상 강제)
_TEST_JWT_SECRET = "test-jwt-secret-32bytes-minimum-value-local-dev-only-0123456789"  # noqa: S105 — 테스트 전용 더미 시크릿
os.environ.setdefault("ONEERP_JWT_SECRET", _TEST_JWT_SECRET)
os.environ.setdefault("ONEERP_DEBUG", "true")

_client = make_service_test_client(_SERVICE_ROOT)


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    """각 테스트마다 @lru_cache 클리어."""
    clear_settings_cache()


@pytest.fixture
def test_client():
    """hr FastAPI 테스트 클라이언트."""
    return _client


@pytest.fixture
def jwt_secret() -> str:
    """공식 JWT 서명 키 (32bytes+)."""
    return _TEST_JWT_SECRET


def _make_jwt(
    *,
    sub: str = "user-hr-admin",
    roles: list[str] | None = None,
    exp_delta: timedelta = timedelta(minutes=30),
    iss: str = "oneerp-gateway",
    aud: str = "oneerp-hr",
    nonce: str | None = None,
    secret: str | None = None,
    algorithm: str = "HS256",
    extra: dict | None = None,
) -> str:
    """테스트용 JWT 생성 헬퍼 — 각 시나리오가 개별 조작."""
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "roles": ["hr_admin"] if roles is None else roles,
        "iat": now,
        "exp": now + exp_delta,
        "iss": iss,
        "aud": aud,
    }
    if nonce is not None:
        payload["nonce"] = nonce
    if extra:
        payload.update(extra)
    return jwt.encode(payload, secret or _TEST_JWT_SECRET, algorithm=algorithm)


@pytest.fixture
def make_jwt():
    """개별 테스트에서 사용할 JWT 팩토리."""
    return _make_jwt
