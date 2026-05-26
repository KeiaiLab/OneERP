"""보험 앱 자동화 — 보험 상태 조회.

모바일 보험 앱에 대한 Appium 기반 자동화를 수행한다.
보험 계약 상태, 보험료 납부 내역 조회를 지원한다.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .appium_manager import AppiumManager

logger = logging.getLogger(__name__)


class InsuranceRunner:
    """보험 앱 자동화 — 보험 상태 조회."""

    # 기본값 — 실제 사용 시 보험사별로 오버라이드
    PACKAGE = ""
    ACTIVITY = ".MainActivity"

    def __init__(self, appium_manager: AppiumManager) -> None:
        self._manager = appium_manager
        self._session_id: str | None = None

    async def start(self, device_id: str, app_package: str = "") -> None:
        """보험 앱 세션 시작."""
        package = app_package or self.PACKAGE
        if not package:
            msg = "app_package가 지정되지 않았습니다."
            raise ValueError(msg)
        try:
            self._session_id = await self._manager.create_android_session(
                device_id=device_id,
                app_package=package,
                app_activity=self.ACTIVITY,
            )
            logger.info("보험 앱 세션 시작 (기기: %s, 패키지: %s)", device_id, package)
        except Exception:
            logger.exception("보험 앱 시작 실패 (기기: %s)", device_id)
            raise

    async def get_insurance_status(self, policy_number: str = "") -> dict:
        """보험 계약 상태 조회."""
        if self._session_id is None:
            msg = "세션이 시작되지 않았습니다."
            raise RuntimeError(msg)
        result: dict = {"success": False, "policies": []}
        try:
            # 계약 조회 메뉴 진입
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.TextView[@text="계약조회"]',
            )
            await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.ListView[@resource-id="policy_list"]',
                timeout=15,
            )
            if policy_number:
                # 특정 계약 검색
                await self._manager.find_and_input(
                    self._session_id,
                    '//android.widget.EditText[@resource-id="policy_no"]',
                    policy_number,
                )
                await self._manager.find_and_click(
                    self._session_id,
                    '//android.widget.Button[@text="조회"]',
                )
                await self._manager.wait_for_element(
                    self._session_id,
                    '//android.widget.ListView[@resource-id="policy_list"]',
                    timeout=15,
                )
            result["success"] = True
            # 스크린샷 캡처
            await self._manager.take_screenshot(self._session_id)
            logger.info("보험 계약 상태 조회 완료")
        except Exception:
            logger.exception("보험 계약 상태 조회 실패")
            if self._session_id:
                await self._manager.take_screenshot(self._session_id)

        return result

    async def get_payment_history(self, policy_number: str) -> list[dict]:
        """보험료 납부 내역 조회."""
        if self._session_id is None:
            msg = "세션이 시작되지 않았습니다."
            raise RuntimeError(msg)
        payments: list[dict] = []
        try:
            # 납부내역 메뉴 진입
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.TextView[@text="납부내역"]',
            )
            await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.EditText[@resource-id="policy_no"]',
            )
            await self._manager.find_and_input(
                self._session_id,
                '//android.widget.EditText[@resource-id="policy_no"]',
                policy_number,
            )
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.Button[@text="조회"]',
            )
            await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.ListView[@resource-id="payment_list"]',
                timeout=20,
            )
            # 스크린샷 캡처
            await self._manager.take_screenshot(self._session_id)
            logger.info("보험료 납부내역 조회 완료: %s", policy_number)
        except Exception:
            logger.exception("보험료 납부내역 조회 실패: %s", policy_number)
            if self._session_id:
                await self._manager.take_screenshot(self._session_id)

        return payments

    async def stop(self) -> None:
        """세션 종료."""
        if self._session_id:
            try:
                await self._manager.close_session(self._session_id)
                logger.info("보험 앱 세션 종료")
            except Exception:
                logger.exception("보험 앱 세션 종료 중 오류")
            finally:
                self._session_id = None
