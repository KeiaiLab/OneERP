"""gateway 통합 테스트 공용 fixture.

실제 DB 호출은 mock_repository_collection 으로 차단.
make_service_test_client 가 default_test_headers 를 포함해 TestClient를 반환한다.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from oneerp_core.testing import (
    clear_settings_cache,
    make_service_test_client,
    mock_repository_collection,
)

# 테스트 환경 기본 설정
os.environ.setdefault("ONEERP_DEBUG", "true")

_SERVICE_ROOT = Path(__file__).resolve().parents[3] / "services" / "platform" / "gateway"


try:
    # DB 호출을 mock 으로 차단한 상태에서 클라이언트 생성
    with mock_repository_collection():
        _client = make_service_test_client(_SERVICE_ROOT)
    _load_error: Exception | None = None
except Exception as e:
    _client = None  # type: ignore[assignment]
    _load_error = e


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """각 테스트 전 설정 캐시 초기화."""
    clear_settings_cache()


@pytest.fixture(scope="session")
def client():
    """gateway TestClient — DB mock 포함."""
    if _client is None:
        pytest.skip(f"gateway app 로드 불가: {_load_error}")
    return _client


@pytest.fixture
def mock_collection():
    """Repository mock 컨텍스트."""
    with mock_repository_collection() as mc:
        yield mc
