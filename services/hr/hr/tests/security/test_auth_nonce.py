"""G3-1 시나리오 5/7 — nonce 중복 차단.

HR 민감 엔드포인트(퇴사·급여 조회 등)는 단발성 토큰(one-time) 을 강제할 수 있다.
nonce 는 한 번만 사용 가능해야 한다.
"""

from __future__ import annotations

import jwt


class _NonceCache:
    """테스트용 nonce 저장소 — 운영에선 Redis 등으로 교체."""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def check_and_store(self, nonce: str) -> bool:
        """처음 보는 nonce 면 저장 후 True, 재사용이면 False."""
        if nonce in self._seen:
            return False
        self._seen.add(nonce)
        return True


def test_동일_nonce_재사용은_차단된다(jwt_secret, make_jwt) -> None:
    """같은 nonce 를 2번째 소비하려 하면 거부."""
    cache = _NonceCache()
    token = make_jwt(nonce="n-once-hr-0001")
    claims = jwt.decode(token, jwt_secret, algorithms=["HS256"], audience="oneerp-hr")

    first = cache.check_and_store(claims["nonce"])
    second = cache.check_and_store(claims["nonce"])

    assert first is True
    assert second is False


def test_서로_다른_nonce는_모두_허용된다(jwt_secret, make_jwt) -> None:
    """서로 다른 nonce 3개는 모두 첫 사용이므로 통과."""
    cache = _NonceCache()
    tokens = [make_jwt(nonce=f"n-{i}") for i in range(3)]
    decoded_nonces = [
        jwt.decode(t, jwt_secret, algorithms=["HS256"], audience="oneerp-hr")["nonce"]
        for t in tokens
    ]
    results = [cache.check_and_store(n) for n in decoded_nonces]
    assert results == [True, True, True]
