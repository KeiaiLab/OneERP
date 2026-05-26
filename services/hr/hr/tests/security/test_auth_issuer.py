"""G3-1 시나리오 4/7 — issuer 검증.

gateway 이외의 발급자가 만든 토큰은 hr 에서 거부해야 한다.
"""

from __future__ import annotations

import jwt
import pytest


def test_잘못된_issuer_토큰은_거부된다(jwt_secret, make_jwt) -> None:
    """iss 가 external-idp 인 토큰은 InvalidIssuerError."""
    token = make_jwt(iss="rogue-idp")
    with pytest.raises(jwt.InvalidIssuerError):
        jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="oneerp-hr",
            issuer="oneerp-gateway",
        )


def test_정상_issuer는_통과한다(jwt_secret, make_jwt) -> None:
    """iss=oneerp-gateway 토큰은 정상 통과 — 대조군."""
    token = make_jwt(iss="oneerp-gateway")
    claims = jwt.decode(
        token,
        jwt_secret,
        algorithms=["HS256"],
        audience="oneerp-hr",
        issuer="oneerp-gateway",
    )
    assert claims["iss"] == "oneerp-gateway"
