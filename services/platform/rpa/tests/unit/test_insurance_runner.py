"""InsuranceRunner 단위 테스트."""

from __future__ import annotations

import asyncio
from typing import cast
from unittest.mock import AsyncMock, MagicMock

import pytest
from oneerp_rpa_app.services.appium_manager import AppiumManager
from oneerp_rpa_app.services.insurance_runner import InsuranceRunner


@pytest.fixture
def mock_appium_manager() -> MagicMock:
    """모든 메서드가 AsyncMock인 AppiumManager를 반환한다."""
    manager = MagicMock(spec=AppiumManager)
    manager.create_android_session = AsyncMock(return_value="test-session-id")
    manager.close_session = AsyncMock()
    manager.find_and_click = AsyncMock(return_value=True)
    manager.find_and_input = AsyncMock(return_value=True)
    manager.wait_for_element = AsyncMock(return_value=True)
    manager.take_screenshot = AsyncMock(return_value=b"fake-png-data")
    return manager


class TestInsuranceRunnerLifecycle:
    """InsuranceRunner 시작/종료 테스트."""

    def test_세션_시작(self, mock_appium_manager: MagicMock) -> None:
        """start() 호출 시 올바른 패키지/액티비티로 세션을 생성한다."""
        runner = InsuranceRunner(cast("AppiumManager", mock_appium_manager))
        asyncio.run(runner.start("device-1", app_package="kr.or.nhis.mobileapp"))

        mock_appium_manager.create_android_session.assert_called_once_with(
            device_id="device-1",
            app_package="kr.or.nhis.mobileapp",
            app_activity=".MainActivity",
        )
        assert runner._session_id == "test-session-id"

    def test_세션_종료(self, mock_appium_manager: MagicMock) -> None:
        """stop() 호출 시 세션이 종료된다."""
        runner = InsuranceRunner(cast("AppiumManager", mock_appium_manager))
        runner._session_id = "test-session-id"
        asyncio.run(runner.stop())

        mock_appium_manager.close_session.assert_called_once_with("test-session-id")
        assert runner._session_id is None

    def test_세션_미시작_에러(self, mock_appium_manager: MagicMock) -> None:
        """세션 없이 조회 시 RuntimeError가 발생한다."""
        runner = InsuranceRunner(cast("AppiumManager", mock_appium_manager))
        with pytest.raises(RuntimeError, match="세션이 시작되지 않았습니다"):
            asyncio.run(runner.get_insurance_status())

    def test_패키지_미지정_에러(self, mock_appium_manager: MagicMock) -> None:
        """app_package 없이 start() 시 ValueError가 발생한다."""
        runner = InsuranceRunner(cast("AppiumManager", mock_appium_manager))
        with pytest.raises(ValueError, match="app_package가 지정되지 않았습니다"):
            asyncio.run(runner.start("device-1"))


class TestInsuranceStatus:
    """보험 계약 상태 조회 테스트."""

    def test_가입현황_조회_정상(self, mock_appium_manager: MagicMock) -> None:
        """보험 계약 상태 조회 시 결과 딕셔너리를 반환한다."""
        runner = InsuranceRunner(cast("AppiumManager", mock_appium_manager))
        runner._session_id = "test-session-id"

        result = asyncio.run(runner.get_insurance_status("123-45-67890"))

        assert isinstance(result, dict)
        assert result["success"] is True
        assert mock_appium_manager.find_and_click.call_count >= 2

    def test_가입현황_조회_세션_없음(self, mock_appium_manager: MagicMock) -> None:
        """세션 없이 조회 시 RuntimeError가 발생한다."""
        runner = InsuranceRunner(cast("AppiumManager", mock_appium_manager))

        with pytest.raises(RuntimeError, match="세션이 시작되지 않았습니다"):
            asyncio.run(runner.get_insurance_status("123-45-67890"))


class TestInsurancePayment:
    """보험료 납부 내역 조회 테스트."""

    def test_납부내역_조회_정상(self, mock_appium_manager: MagicMock) -> None:
        """납부 내역 조회가 에러 없이 실행된다."""
        runner = InsuranceRunner(cast("AppiumManager", mock_appium_manager))
        runner._session_id = "test-session-id"

        result = asyncio.run(runner.get_payment_history("123-45-67890"))

        assert isinstance(result, list)
        assert mock_appium_manager.find_and_click.call_count >= 2
        assert mock_appium_manager.find_and_input.call_count >= 1

    def test_납부내역_조회_세션_없음(self, mock_appium_manager: MagicMock) -> None:
        """세션 없이 조회 시 RuntimeError가 발생한다."""
        runner = InsuranceRunner(cast("AppiumManager", mock_appium_manager))

        with pytest.raises(RuntimeError, match="세션이 시작되지 않았습니다"):
            asyncio.run(runner.get_payment_history("123-45-67890"))
