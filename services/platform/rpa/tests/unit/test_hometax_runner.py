"""HometaxRunner 단위 테스트."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from oneerp_rpa_app.services.appium_manager import AppiumManager
from oneerp_rpa_app.services.hometax_runner import HometaxRunner


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


class TestHometaxRunnerLifecycle:
    """HometaxRunner 시작/종료 테스트."""

    def test_세션_시작(self, mock_appium_manager: MagicMock) -> None:
        """start() 호출 시 올바른 패키지/액티비티로 세션을 생성한다."""
        runner = HometaxRunner(mock_appium_manager)
        asyncio.run(runner.start("device-1"))

        mock_appium_manager.create_android_session.assert_called_once_with(
            device_id="device-1",
            app_package="kr.go.nts.hometax",
            app_activity=".MainActivity",
        )
        assert runner._session_id == "test-session-id"

    def test_세션_종료(self, mock_appium_manager: MagicMock) -> None:
        """stop() 호출 시 세션이 종료된다."""
        runner = HometaxRunner(mock_appium_manager)
        runner._session_id = "test-session-id"
        asyncio.run(runner.stop())

        mock_appium_manager.close_session.assert_called_once_with("test-session-id")
        assert runner._session_id is None

    def test_세션_없이_종료(self, mock_appium_manager: MagicMock) -> None:
        """세션이 없는 상태에서 stop()은 에러 없이 처리된다."""
        runner = HometaxRunner(mock_appium_manager)
        asyncio.run(runner.stop())
        mock_appium_manager.close_session.assert_not_called()


class TestHometaxLogin:
    """홈택스 로그인 테스트."""

    def test_로그인_성공(self, mock_appium_manager: MagicMock) -> None:
        """정상 로그인 시 True를 반환한다."""
        runner = HometaxRunner(mock_appium_manager)
        runner._session_id = "test-session-id"

        result = asyncio.run(runner.login("test-password"))

        assert result is True
        # 로그인 버튼 클릭, 공동인증서 선택, 비밀번호 입력, 확인 버튼 클릭이 호출되어야 함
        assert mock_appium_manager.find_and_click.call_count >= 3
        assert mock_appium_manager.find_and_input.call_count >= 1

    def test_로그인_세션_없음(self, mock_appium_manager: MagicMock) -> None:
        """세션 없이 로그인 시 RuntimeError가 발생한다."""
        runner = HometaxRunner(mock_appium_manager)

        with pytest.raises(RuntimeError, match="세션이 시작되지 않았습니다"):
            asyncio.run(runner.login("test-password"))

    def test_로그인_실패(self, mock_appium_manager: MagicMock) -> None:
        """로그인 완료 요소를 찾지 못하면 False를 반환한다."""
        runner = HometaxRunner(mock_appium_manager)
        runner._session_id = "test-session-id"

        # 마이홈택스 텍스트를 찾지 못하면 로그인 실패
        mock_appium_manager.wait_for_element = AsyncMock(
            side_effect=[True, True, False],
        )

        result = asyncio.run(runner.login("wrong-password"))

        assert result is False


class TestTaxInvoice:
    """세금계산서 발급/조회 테스트."""

    def test_세금계산서_발급(self, mock_appium_manager: MagicMock) -> None:
        """세금계산서 발급 시 결과 딕셔너리를 반환한다."""
        runner = HometaxRunner(mock_appium_manager)
        runner._session_id = "test-session-id"

        invoice_data = {
            "supplier": {"business_number": "1234567890"},
            "buyer": {"business_number": "9876543210"},
            "items": [{"name": "컨설팅", "amount": 1000000}],
        }

        result = asyncio.run(runner.issue_tax_invoice(invoice_data))

        assert result["success"] is True
        assert mock_appium_manager.find_and_click.call_count >= 2
        assert mock_appium_manager.find_and_input.call_count >= 2

    def test_세금계산서_발급_세션_없음(self, mock_appium_manager: MagicMock) -> None:
        """세션 없이 발급 시 RuntimeError가 발생한다."""
        runner = HometaxRunner(mock_appium_manager)

        with pytest.raises(RuntimeError, match="세션이 시작되지 않았습니다"):
            asyncio.run(runner.issue_tax_invoice({}))

    def test_세금계산서_조회(self, mock_appium_manager: MagicMock) -> None:
        """세금계산서 조회가 에러 없이 실행된다."""
        runner = HometaxRunner(mock_appium_manager)
        runner._session_id = "test-session-id"

        result = asyncio.run(runner.query_tax_invoices("2026-01"))

        assert isinstance(result, list)

    def test_세금계산서_조회_세션_없음(self, mock_appium_manager: MagicMock) -> None:
        """세션 없이 조회 시 RuntimeError가 발생한다."""
        runner = HometaxRunner(mock_appium_manager)

        with pytest.raises(RuntimeError, match="세션이 시작되지 않았습니다"):
            asyncio.run(runner.query_tax_invoices("2026-01"))
