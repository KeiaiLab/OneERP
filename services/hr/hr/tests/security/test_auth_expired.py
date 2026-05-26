"""G3-1 시나리오 1/7 — 만료된 JWT 거부.

HR 는 개인정보 보호 중요도가 높아 토큰 수명 검증이 특히 엄격해야 한다.
"""

from __future__ import annotations

from datetime import timedelta

import jwt
import pytest


def test_expired_jwt는_decode단계에서_거부된다(jwt_secret, make_jwt) -> None:
    """만료 시간이 과거인 JWT 는 `jwt.decode` 에서 ExpiredSignatureError 를 던져야 한다."""
    token = make_jwt(exp_delta=timedelta(seconds=-60))
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(token, jwt_secret, algorithms=["HS256"], audience="oneerp-hr")


def test_유효한_JWT는_decode성공한다(jwt_secret, make_jwt) -> None:
    """정상 JWT 는 decode 성공하여 roles 가 보존되어야 한다 — 대조군."""
    token = make_jwt(roles=["hr_admin"], exp_delta=timedelta(minutes=5))
    claims = jwt.decode(token, jwt_secret, algorithms=["HS256"], audience="oneerp-hr")
    assert "hr_admin" in claims["roles"]
