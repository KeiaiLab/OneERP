"""은행 앱 E2E 시나리오."""

from __future__ import annotations

import asyncio

import pytest
from oneerp_rpa_app.services.banking_runner import BankingRunner

pytestmark = [pytest.mark.e2e, pytest.mark.appium]

# 테스트에 사용할 뱅킹 앱 패키지
KB_PACKAGE = "com.kbstar.kbbank"


class TestBankingE2EFlow:
    """뱅킹 앱 E2E 흐름."""

    def test_은행_앱_세션_시작(self, appium_manager):
        """은행 앱 세션을 시작한다."""
        runner = BankingRunner(appium_manager)
        asyncio.run(runner.start("emulator-5554", app_package=KB_PACKAGE))
        assert runner._session_id is not None

    def test_잔액_조회(self, appium_manager):
        """계좌 잔액을 조회한다."""
        runner = BankingRunner(appium_manager)
        asyncio.run(runner.start("emulator-5554", app_package=KB_PACKAGE))
        balance = asyncio.run(runner.get_balance("110-123-456789"))
        assert isinstance(balance, dict)
        assert "account_number" in balance
        asyncio.run(runner.stop())

    def test_거래내역_조회(self, appium_manager):
        """계좌 거래내역을 조회한다."""
        runner = BankingRunner(appium_manager)
        asyncio.run(runner.start("emulator-5554", app_package=KB_PACKAGE))
        transactions = asyncio.run(runner.get_transactions("110-123-456789", "2026-03"))
        assert isinstance(transactions, list)
        asyncio.run(runner.stop())

    def test_세션_미시작_잔액_조회_에러(self, appium_manager):
        """세션 없이 잔액 조회 시 RuntimeError 발생."""
        runner = BankingRunner(appium_manager)
        with pytest.raises(RuntimeError, match="세션이 시작되지 않았습니다"):
            asyncio.run(runner.get_balance("110-123-456789"))

    def test_패키지_미지정_에러(self, appium_manager):
        """app_package 없이 시작 시 ValueError 발생."""
        runner = BankingRunner(appium_manager)
        with pytest.raises(ValueError, match="app_package가 지정되지 않았습니다"):
            asyncio.run(runner.start("emulator-5554"))
