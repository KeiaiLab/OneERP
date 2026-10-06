"""비밀번호 해시 — scrypt + 무작위 salt.

저장 형식: ``scrypt$<n>$<r>$<p>$<salt hex>$<key hex>``
예: ``scrypt$16384$8$1$9f0c…$4be1…``

레거시 SHA-256 hex 해시는 검증만 지원하고, 로그인 성공 시 scrypt 로 교체한다
(``needs_rehash``). 새 해시는 언제나 scrypt 다.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets

_SCHEME = "scrypt"
_SEP = "$"
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SALT_BYTES = 16
_KEY_BYTES = 32
_FIELD_COUNT = 6
_LEGACY_HEX_LEN = 64


def _derive(password: str, salt: bytes, n: int, r: int, p: int) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=n, r=r, p=p, dklen=_KEY_BYTES)


def hash_password(password: str) -> str:
    """비밀번호를 scrypt 로 해시한다."""
    salt = secrets.token_bytes(_SALT_BYTES)
    key = _derive(password, salt, _SCRYPT_N, _SCRYPT_R, _SCRYPT_P)
    fields = [_SCHEME, str(_SCRYPT_N), str(_SCRYPT_R), str(_SCRYPT_P), salt.hex(), key.hex()]
    return _SEP.join(fields)


def _verify_scrypt(password: str, stored: str) -> bool:
    fields = stored.split(_SEP)
    if len(fields) != _FIELD_COUNT:
        return False

    _, n, r, p, salt_hex, key_hex = fields
    try:
        key = _derive(password, bytes.fromhex(salt_hex), int(n), int(r), int(p))
        expected = bytes.fromhex(key_hex)
    except ValueError:
        return False
    return hmac.compare_digest(key, expected)


def _verify_legacy(password: str, stored: str) -> bool:
    # 마이그레이션 전용 — 기존 SHA-256 저장분을 확인해 scrypt 로 올리기 위해서만 쓴다.
    digest = hashlib.sha256(password.encode()).hexdigest()
    return hmac.compare_digest(digest, stored)


def verify_password(password: str, stored: str) -> bool:
    """저장된 해시(scrypt 또는 레거시 SHA-256)와 비밀번호를 상수 시간 비교한다."""
    if stored.startswith(_SCHEME + _SEP):
        return _verify_scrypt(password, stored)
    if len(stored) == _LEGACY_HEX_LEN:
        return _verify_legacy(password, stored)
    return False


def needs_rehash(stored: str) -> bool:
    """현재 scrypt 파라미터가 아닌 해시면 True — 로그인 성공 시 교체 대상."""
    prefix = _SEP.join([_SCHEME, str(_SCRYPT_N), str(_SCRYPT_R), str(_SCRYPT_P)]) + _SEP
    return not stored.startswith(prefix)
