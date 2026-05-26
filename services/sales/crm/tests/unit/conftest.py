"""crm 단위 테스트 공통 fixture.

M1 공통화 — `oneerp_core.testing` 팩토리 기반.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from types import ModuleType

import pytest
from oneerp_core.testing import (
    clear_settings_cache,
    make_service_test_client,
    mock_repository_collection,
)

os.environ.setdefault("ONEERP_DEBUG", "true")

_SERVICE_ROOT = Path(__file__).resolve().parents[2]
_client = make_service_test_client(_SERVICE_ROOT)

# M1-2 후속 — fixture 가 참조하는 module-level 변수 (sys.modules 에서 조회)
_leads_mod: ModuleType = sys.modules["oneerp_crm_app.routes.leads"]
_opportunities_mod: ModuleType = sys.modules["oneerp_crm_app.routes.opportunities"]
_issues_mod: ModuleType = sys.modules["oneerp_crm_app.routes.issues"]
_services_mod: ModuleType = sys.modules["oneerp_crm_app.routes.services"]


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    clear_settings_cache()


@pytest.fixture
def mock_collection():
    with mock_repository_collection() as mc:
        yield mc


@pytest.fixture
def test_client():
    return _client


@pytest.fixture
def leads_mod() -> ModuleType:
    """리드 라우터 모듈 참조를 반환한다."""
    return _leads_mod


@pytest.fixture
def opportunities_mod() -> ModuleType:
    """기회 라우터 모듈 참조를 반환한다."""
    return _opportunities_mod


@pytest.fixture
def issues_mod() -> ModuleType:
    """이슈 라우터 모듈 참조를 반환한다."""
    return _issues_mod


@pytest.fixture
def services_mod() -> ModuleType:
    """서비스 레지스트리 라우터 모듈 참조를 반환한다."""
    return _services_mod
