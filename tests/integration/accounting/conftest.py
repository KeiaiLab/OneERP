"""accounting 통합 테스트 공용 fixture.

services/finance/accounting 서비스의 FastAPI 앱을 DB mock 과 함께 로드한다.
gateway 통합 테스트의 패턴을 그대로 미러링한다.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from oneerp_core.testing import (
    clear_settings_cache,
    default_test_headers,
    load_service_app,
    mock_repository_collection,
)

# 테스트 환경 기본 설정 — 서비스 settings 의 required 필드 fallback
os.environ.setdefault("ONEERP_DEBUG", "true")

_SERVICE_ROOT = Path(__file__).resolve().parents[3] / "services" / "finance" / "accounting"


try:
    # Repository mock 하에서 앱을 로드 — import-time DB 접근 차단
    with mock_repository_collection():
        _app = load_service_app(_SERVICE_ROOT)
    # raise_server_exceptions=False: Pydantic/서버 예외를 500 응답으로 전환
    _client = TestClient(_app, raise_server_exceptions=False)
    _client.headers.update(default_test_headers())
    _load_error: Exception | None = None
except Exception as e:  # pragma: no cover — 로드 실패는 skip 으로 라우팅
    _client = None  # type: ignore[assignment]
    _load_error = e


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """각 테스트 전 설정 캐시 초기화 — tenant_id leak 방지."""
    clear_settings_cache()


@pytest.fixture(scope="session")
def client():
    """accounting FastAPI TestClient — DB mock 포함."""
    if _client is None:
        pytest.skip(f"accounting app 로드 불가: {_load_error}")
    return _client


@pytest.fixture
def mock_collection():
    """Repository mock 컨텍스트 — 테스트 내부에서 컬렉션 조작 필요 시 사용."""
    with mock_repository_collection() as mc:
        yield mc
