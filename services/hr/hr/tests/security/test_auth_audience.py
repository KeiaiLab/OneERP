"""G3-1 시나리오 3/7 — audience 검증.

gateway 가 다른 서비스(accounting 등) 용 토큰을 발급한 경우 hr 는 거부해야 한다.
"""

from __future__ import annotations

import jwt
import pytest


def test_다른_audience_토큰은_거부된다(jwt_secret, make_jwt) -> None:
    """aud=oneerp-accounting 토큰을 hr 가 소비하면 InvalidAudienceError."""
    token = make_jwt(aud="oneerp-accounting")
    with pytest.raises(jwt.InvalidAudienceError):
        jwt.decode(token, jwt_secret, algorithms=["HS256"], audience="oneerp-hr")


def test_aud_claim_누락_토큰은_거부된다(jwt_secret) -> None:
    """aud claim 없는 토큰은 MissingRequiredClaimError."""
    token = jwt.encode({"sub": "u", "roles": ["hr_admin"]}, jwt_secret, algorithm="HS256")
    with pytest.raises(jwt.MissingRequiredClaimError):
        jwt.decode(
            token,
            jwt_secret,
            algorithms=["HS256"],
            audience="oneerp-hr",
            options={"require": ["aud"]},
        )
