"""G3-1 시나리오 2/7 — 위조 서명 거부.

HR 는 직원 마스터/급여 데이터에 접근하므로 서명 위조는 심각한 위협이다.
"""

from __future__ import annotations

import jwt
import pytest


def test_다른_시크릿으로_서명된_JWT는_거부된다(jwt_secret, make_jwt) -> None:
    """공격자가 다른 시크릿으로 서명한 JWT 는 InvalidSignatureError 를 던진다."""
    attacker_secret = "attacker-secret-32bytes-value-should-not-be-accepted-xx"  # noqa: S105 — 테스트 공격 시뮬
    forged = make_jwt(secret=attacker_secret, roles=["hr_admin"])
    with pytest.raises(jwt.InvalidSignatureError):
        jwt.decode(forged, jwt_secret, algorithms=["HS256"], audience="oneerp-hr")


def test_none_알고리즘_JWT는_거부된다(jwt_secret) -> None:
    """`alg=none` 공격 — jwt 라이브러리는 HS256 로만 decode 하므로 거부."""
    payload_part = "eyJzdWIiOiJhdHRhY2tlciIsInJvbGVzIjpbImhyX2FkbWluIl19"
    none_token = f"eyJhbGciOiJub25lIn0.{payload_part}."
    with pytest.raises(jwt.InvalidAlgorithmError):
        jwt.decode(none_token, jwt_secret, algorithms=["HS256"], audience="oneerp-hr")
