"""AppiumManager 단위 테스트."""

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock, patch

import pytest
from oneerp_rpa_app.services.appium_manager import AppiumManager


class TestGetConnectedDevices:
    """get_connected_devices 메서드 테스트."""

    def test_adb_정상_출력_파싱(self) -> None:
        """ADB 출력에서 연결된 기기 목록을 정상적으로 파싱한다."""
        mock_result = MagicMock()
        mock_result.stdout = (
            "List of devices attached\n"
            "emulator-5554          device product:sdk_gphone64 model:sdk_gphone64 transport_id:1\n"
            "R5CT1234567            device product:beyond2lte model:SM_G975F transport_id:2\n"
        )
        with patch("subprocess.run", return_value=mock_result):
            manager = AppiumManager()
            devices = manager.get_connected_devices()

        assert len(devices) == 2
        assert devices[0]["id"] == "emulator-5554"
        assert devices[0]["status"] == "connected"
        assert devices[0]["model"] == "sdk_gphone64"
        assert devices[1]["id"] == "R5CT1234567"

    def test_adb_미설치(self) -> None:
        """ADB가 설치되지 않았을 때 빈 목록을 반환한다."""
        with patch("subprocess.run", side_effect=FileNotFoundError):
            manager = AppiumManager()
            devices = manager.get_connected_devices()

        assert devices == []

    def test_adb_타임아웃(self) -> None:
        """ADB 실행이 시간 초과되면 빈 목록을 반환한다."""
        import subprocess

        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="adb", timeout=10)):
            manager = AppiumManager()
            devices = manager.get_connected_devices()

        assert devices == []

    def test_연결된_기기_없음(self) -> None:
        """연결된 기기가 없으면 빈 목록을 반환한다."""
        mock_result = MagicMock()
        mock_result.stdout = "List of devices attached\n\n"
        with patch("subprocess.run", return_value=mock_result):
            manager = AppiumManager()
            devices = manager.get_connected_devices()

        assert devices == []


class TestSessionManagement:
    """세션 생성/종료 테스트."""

    def test_세션_등록_확인(self) -> None:
        """세션이 active_sessions에 등록되는지 확인한다."""
        mock_driver = MagicMock()
        manager = AppiumManager()
        manager._active_sessions["test-session-123"] = mock_driver

        assert "test-session-123" in manager._active_sessions

    def test_세션_종료(self) -> None:
        """세션 종료 시 드라이버가 정리된다."""
        mock_driver = MagicMock()
        manager = AppiumManager()
        manager._active_sessions["session-1"] = mock_driver

        asyncio.run(manager.close_session("session-1"))

        mock_driver.quit.assert_called_once()
        assert "session-1" not in manager._active_sessions

    def test_존재하지_않는_세션_종료(self) -> None:
        """존재하지 않는 세션 종료 시 에러 없이 처리된다."""
        manager = AppiumManager()
        asyncio.run(manager.close_session("nonexistent-session"))

    def test_스크린샷_세션_없음(self) -> None:
        """세션이 없는 상태에서 스크린샷 시도 시 ValueError가 발생한다."""
        manager = AppiumManager()
        with pytest.raises(ValueError, match="세션을 찾을 수 없음"):
            asyncio.run(manager.take_screenshot("nonexistent"))

    def test_find_and_click_세션_없음(self) -> None:
        """세션이 없는 상태에서 클릭 시도 시 ValueError가 발생한다."""
        manager = AppiumManager()
        with pytest.raises(ValueError, match="세션을 찾을 수 없음"):
            asyncio.run(manager.find_and_click("nonexistent", "//button"))

    def test_find_and_input_세션_없음(self) -> None:
        """세션이 없는 상태에서 입력 시도 시 ValueError가 발생한다."""
        manager = AppiumManager()
        with pytest.raises(ValueError, match="세션을 찾을 수 없음"):
            asyncio.run(manager.find_and_input("nonexistent", "//input", "text"))

    def test_wait_for_element_세션_없음(self) -> None:
        """세션이 없는 상태에서 대기 시도 시 ValueError가 발생한다."""
        manager = AppiumManager()
        with pytest.raises(ValueError, match="세션을 찾을 수 없음"):
            asyncio.run(manager.wait_for_element("nonexistent", "//div"))
