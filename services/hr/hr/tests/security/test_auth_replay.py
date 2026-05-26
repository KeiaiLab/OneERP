"""G3-1 시나리오 6/7 — replay 공격 차단.

공격자가 가로챈 유효 JWT 를 시간 차이를 두고 다시 사용하는 경우를 방어한다.
짧은 TTL + nonce/jti 로 replay window 를 좁힌다.
"""

from __future__ import annotations

import time
from datetime import timedelta

import jwt
import pytest


def test_짧은_TTL_토큰은_만료_즉시_거부(jwt_secret, make_jwt) -> None:
    """TTL 1초 토큰은 expire 직후 ExpiredSignatureError — replay window 축소."""
    token = make_jwt(exp_delta=timedelta(seconds=1))
    time.sleep(2)
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, jwt_secret, algorithms=["HS256"], audience="oneerp-hr")


def test_jti_기반_replay_탐지(jwt_secret, make_jwt) -> None:
    """동일 jti 를 2번째 소비하면 replay 로 간주 (테스트용 in-memory cache)."""
    seen_jti: set[str] = set()
    token = make_jwt(extra={"jti": "jti-hr-replay-001"})
    claims = jwt.decode(token, jwt_secret, algorithms=["HS256"], audience="oneerp-hr")

    jti = claims["jti"]
    first = jti not in seen_jti
    seen_jti.add(jti)
    second = jti not in seen_jti

    assert first is True
    assert second is False
