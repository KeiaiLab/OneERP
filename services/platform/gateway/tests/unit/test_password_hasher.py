"""password_hasher 단위 테스트."""

from __future__ import annotations

from oneerp_gateway_app.services.password_hasher import (
    hash_password,
    needs_rehash,
    verify_password,
)

_PLAIN = "secret"
# 레거시 SHA-256("secret") — 마이그레이션 전 저장분 형식.
_LEGACY = "2bb80d537b1da3e38bd30361aa855686bde0eacd7162fef6a25fe97bf527a25b"


def test_scrypt_해시는_검증되고_재해시가_불필요하다() -> None:
    stored = hash_password(_PLAIN)

    assert stored.startswith("scrypt$")
    assert verify_password(_PLAIN, stored)
    assert not verify_password("wrong", stored)
    assert not needs_rehash(stored)


def test_같은_비밀번호도_salt로_해시가_다르다() -> None:
    assert hash_password(_PLAIN) != hash_password(_PLAIN)


def test_레거시_해시는_검증되고_재해시_대상이다() -> None:
    assert verify_password(_PLAIN, _LEGACY)
    assert not verify_password("wrong", _LEGACY)
    assert needs_rehash(_LEGACY)


def test_형식이_깨진_해시는_거부한다() -> None:
    assert not verify_password(_PLAIN, "")
    assert not verify_password(_PLAIN, "scrypt$bad")
    assert not verify_password(_PLAIN, "scrypt$16384$8$1$zz$zz")
