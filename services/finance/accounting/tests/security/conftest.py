"""accounting 보안 테스트 공통 fixture — G3-1 AuthN 7 종 scaffolding.

로컬 환경에서는 스테이징 인프라(Keycloak·OPA)가 없으므로 대부분의 케이스가
`skip` 으로 통과한다. 스테이징 활성화 시 `ONEERP_STAGING_AVAILABLE=1` 로
실제 401 검증을 수행한다.
"""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def staging_available() -> bool:
    """스테이징 인프라 활성화 여부."""
    return os.environ.get("ONEERP_STAGING_AVAILABLE", "").lower() in {"1", "true", "yes"}


@pytest.fixture(scope="session")
def accounting_client() -> Generator[TestClient]:
    """accounting TestClient — 헤더 주입 없이 raw 요청."""
    os.environ.setdefault(
        "ONEERP_JWT_SECRET",
        "dev-secret-minimum-32-bytes-for-local-security-tests-only",
    )
    os.environ.setdefault("ONEERP_DEBUG", "true")

    from oneerp_accounting_app.main import app  # 환경변수 주입 후 import

    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def protected_path() -> str:
    """보호된 대표 엔드포인트 경로 — 전표 조회(테넌트 컨텍스트 필수)."""
    return "/api/v1/journal-entries"
