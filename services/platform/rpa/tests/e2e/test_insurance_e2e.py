"""4대보험 앱 E2E 시나리오."""

from __future__ import annotations

import asyncio

import pytest
from oneerp_rpa_app.services.insurance_runner import InsuranceRunner

pytestmark = [pytest.mark.e2e, pytest.mark.appium]

# 테스트에 사용할 보험 앱 패키지
INSURANCE_PACKAGE = "kr.or.nhis.mobileapp"


class TestInsuranceE2EFlow:
    """보험 앱 E2E 흐름."""

    def test_보험_앱_세션_시작(self, appium_manager):
        """보험 앱 세션을 시작한다."""
        runner = InsuranceRunner(appium_manager)
        asyncio.run(runner.start("emulator-5554", app_package=INSURANCE_PACKAGE))
        assert runner._session_id is not None

    def test_가입현황_조회(self, appium_manager):
        """보험 계약 상태를 조회한다."""
        runner = InsuranceRunner(appium_manager)
        asyncio.run(runner.start("emulator-5554", app_package=INSURANCE_PACKAGE))
        status = asyncio.run(runner.get_insurance_status("123-45-67890"))
        assert isinstance(status, dict)
        assert "success" in status
        asyncio.run(runner.stop())

    def test_납부내역_조회(self, appium_manager):
        """보험료 납부 내역을 조회한다."""
        runner = InsuranceRunner(appium_manager)
        asyncio.run(runner.start("emulator-5554", app_package=INSURANCE_PACKAGE))
        payments = asyncio.run(runner.get_payment_history("123-45-67890"))
        assert isinstance(payments, list)
        asyncio.run(runner.stop())

    def test_세션_미시작_가입현황_에러(self, appium_manager):
        """세션 없이 조회 시 RuntimeError 발생."""
        runner = InsuranceRunner(appium_manager)
        with pytest.raises(RuntimeError, match="세션이 시작되지 않았습니다"):
            asyncio.run(runner.get_insurance_status())

    def test_패키지_미지정_에러(self, appium_manager):
        """app_package 없이 시작 시 ValueError 발생."""
        runner = InsuranceRunner(appium_manager)
        with pytest.raises(ValueError, match="app_package가 지정되지 않았습니다"):
            asyncio.run(runner.start("emulator-5554"))
