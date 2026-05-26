"""Appium E2E 테스트 fixture -- 실제 기기/에뮬레이터 연결."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_RPA_ROOT = str(Path(__file__).resolve().parents[2])

# 다른 서비스의 app 패키지 경로를 sys.path에서 제거하여 충돌 방지
_removed: list[str] = []
for _p in list(sys.path):
    if "/services/" in _p and "/rpa" not in _p:
        _removed.append(_p)
        sys.path.remove(_p)

# 기존에 로드된 다른 서비스의 app 모듈 제거
for _key in [k for k in sys.modules if k == "app" or k.startswith("oneerp_rpa_app.")]:
    del sys.modules[_key]

# rpa 서비스를 sys.path 최우선에 추가
if _RPA_ROOT not in sys.path:
    sys.path.insert(0, _RPA_ROOT)

# 제거했던 경로 복원
sys.path.extend(_removed)

logger = logging.getLogger(__name__)

# Appium 서버 URL (실제 기기 연결 시 사용)
APPIUM_URL = os.environ.get("APPIUM_URL", "http://localhost:4723")
# 테스트 기기 ID (adb devices에서 확인)
DEVICE_ID = os.environ.get("TEST_DEVICE_ID", "emulator-5554")
# 실제 기기 연결 여부
USE_REAL_DEVICE = os.environ.get("USE_REAL_DEVICE", "false").lower() == "true"


@pytest.fixture
def appium_manager():
    """AppiumManager 인스턴스 -- 실제 또는 Mock."""
    if USE_REAL_DEVICE:
        from oneerp_rpa_app.services.appium_manager import AppiumManager

        return AppiumManager(appium_url=APPIUM_URL)

    # Mock 모드 -- 실제 기기 없이 흐름 검증
    manager = MagicMock()
    manager.create_android_session = AsyncMock(return_value="mock-session")
    manager.close_session = AsyncMock()
    manager.find_and_click = AsyncMock(return_value=True)
    manager.find_and_input = AsyncMock(return_value=True)
    manager.wait_for_element = AsyncMock(return_value=True)
    manager.take_screenshot = AsyncMock(return_value=b"\x89PNG\r\n\x1a\n")
    manager.get_connected_devices.return_value = [
        {"device_id": DEVICE_ID, "status": "device", "model": "Pixel_7"},
    ]
    return manager


@pytest.fixture
def screenshots_dir(tmp_path):
    """스크린샷 저장 디렉토리."""
    d = tmp_path / "screenshots"
    d.mkdir()
    return d
