"""hr 통합 테스트 공용 fixture.

services/hr/hr FastAPI 앱을 DB mock 과 함께 로드한다.
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

os.environ.setdefault("ONEERP_DEBUG", "true")

_SERVICE_ROOT = Path(__file__).resolve().parents[3] / "services" / "hr" / "hr"


try:
    with mock_repository_collection():
        _app = load_service_app(_SERVICE_ROOT)
    # raise_server_exceptions=False: 서버 내부 예외를 500 응답으로 전환
    _client = TestClient(_app, raise_server_exceptions=False)
    _client.headers.update(default_test_headers())
    _load_error: Exception | None = None
except Exception as e:  # pragma: no cover
    _client = None  # type: ignore[assignment]
    _load_error = e


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """각 테스트 전 설정 캐시 초기화."""
    clear_settings_cache()


@pytest.fixture(scope="session")
def client():
    """hr FastAPI TestClient — DB mock 포함."""
    if _client is None:
        pytest.skip(f"hr app 로드 불가: {_load_error}")
    return _client


@pytest.fixture
def mock_collection():
    """Repository mock 컨텍스트."""
    with mock_repository_collection() as mc:
        yield mc
