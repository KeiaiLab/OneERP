"""홈택스 전자세금계산서 E2E 시나리오.

실제 기기: USE_REAL_DEVICE=true APPIUM_URL=http://... TEST_DEVICE_ID=... pytest
Mock 모드: 기본 (흐름 검증만)
"""

from __future__ import annotations

import asyncio

import pytest
from oneerp_rpa_app.services.hometax_runner import HometaxRunner

pytestmark = [pytest.mark.e2e, pytest.mark.appium]


class TestHometaxE2EFlow:
    """홈택스 전자세금계산서 전체 E2E 흐름."""

    def test_홈택스_앱_세션_시작(self, appium_manager):
        """홈택스 앱 세션을 시작한다."""
        runner = HometaxRunner(appium_manager)
        asyncio.run(runner.start("emulator-5554"))
        assert runner._session_id is not None

    def test_홈택스_로그인(self, appium_manager):
        """공동인증서로 홈택스에 로그인한다."""
        runner = HometaxRunner(appium_manager)
        asyncio.run(runner.start("emulator-5554"))
        result = asyncio.run(runner.login("test-cert-password"))
        assert result is True

    def test_세금계산서_발급_전체_흐름(self, appium_manager, screenshots_dir):
        """세금계산서 발급 전체 흐름: 시작->로그인->발급->스크린샷->검증."""
        runner = HometaxRunner(appium_manager)

        # Step 1: 앱 시작
        asyncio.run(runner.start("emulator-5554"))

        # Step 2: 로그인
        login_ok = asyncio.run(runner.login("test-cert-password"))
        assert login_ok

        # Step 3: 세금계산서 발급
        invoice_data = {
            "supplier": {"business_number": "1234567890"},
            "buyer": {"business_number": "0987654321"},
            "items": [
                {"name": "테스트품목", "amount": 1000000},
            ],
        }
        result = asyncio.run(runner.issue_tax_invoice(invoice_data))

        # Step 4: 결과 검증
        assert result is not None
        assert isinstance(result, dict)
        assert "success" in result

        # Step 5: 세션 종료
        asyncio.run(runner.stop())

    def test_세금계산서_조회(self, appium_manager):
        """기간별 세금계산서 목록을 조회한다."""
        runner = HometaxRunner(appium_manager)
        asyncio.run(runner.start("emulator-5554"))
        asyncio.run(runner.login("test-cert-password"))

        invoices = asyncio.run(runner.query_tax_invoices("2026-03"))
        assert isinstance(invoices, list)

        asyncio.run(runner.stop())

    def test_세션_미시작_에러(self, appium_manager):
        """세션 시작 없이 로그인 시 RuntimeError 발생."""
        runner = HometaxRunner(appium_manager)
        with pytest.raises(RuntimeError, match="세션이 시작되지 않았습니다"):
            asyncio.run(runner.login("password"))
