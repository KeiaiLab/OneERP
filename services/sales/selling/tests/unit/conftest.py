"""selling 단위 테스트 공통 fixture.

M1 공통화 — `oneerp_core.testing` 팩토리 기반.
"""

from __future__ import annotations

import importlib
import os
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
_qtn_mod = importlib.import_module("oneerp_selling_app.routes.quotations")
_so_mod = importlib.import_module("oneerp_selling_app.routes.sales_orders")


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
def quotations_mod() -> ModuleType:
    """견적서 라우터 모듈 참조를 반환한다."""
    return _qtn_mod


@pytest.fixture
def sales_orders_mod() -> ModuleType:
    """판매주문 라우터 모듈 참조를 반환한다."""
    return _so_mod
