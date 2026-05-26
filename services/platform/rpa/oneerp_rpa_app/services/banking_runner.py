"""뱅킹 앱 자동화 — 계좌 거래내역 조회/잔액 확인.

모바일 뱅킹 앱에 대한 Appium 기반 자동화를 수행한다.
거래내역 조회, 잔액 확인을 지원한다.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .appium_manager import AppiumManager

logger = logging.getLogger(__name__)


class BankingRunner:
    """뱅킹 앱 자동화 — 거래내역 조회/잔액 확인."""

    # 기본값 — 실제 사용 시 은행별로 오버라이드
    PACKAGE = ""
    ACTIVITY = ".MainActivity"

    def __init__(self, appium_manager: AppiumManager) -> None:
        self._manager = appium_manager
        self._session_id: str | None = None

    async def start(self, device_id: str, app_package: str = "") -> None:
        """뱅킹 앱 세션 시작."""
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
            logger.info("뱅킹 앱 세션 시작 (기기: %s, 패키지: %s)", device_id, package)
        except Exception:
            logger.exception("뱅킹 앱 시작 실패 (기기: %s)", device_id)
            raise

    async def get_balance(self, account_number: str) -> dict:
        """계좌 잔액 조회."""
        if self._session_id is None:
            msg = "세션이 시작되지 않았습니다."
            raise RuntimeError(msg)
        result: dict = {"success": False, "account_number": account_number, "balance": 0}
        try:
            # 잔액 조회 메뉴 진입
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.TextView[@text="잔액조회"]',
            )
            await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.EditText[@resource-id="account_no"]',
            )
            # 계좌번호 입력
            await self._manager.find_and_input(
                self._session_id,
                '//android.widget.EditText[@resource-id="account_no"]',
                account_number,
            )
            # 조회 실행
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.Button[@text="조회"]',
            )
            await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.TextView[@resource-id="balance"]',
                timeout=15,
            )
            result["success"] = True
            # 스크린샷 캡처
            await self._manager.take_screenshot(self._session_id)
            logger.info("잔액 조회 완료: %s", account_number)
        except Exception:
            logger.exception("잔액 조회 실패: %s", account_number)
            if self._session_id:
                await self._manager.take_screenshot(self._session_id)

        return result

    async def get_transactions(self, account_number: str, period: str) -> list[dict]:
        """거래내역 조회."""
        if self._session_id is None:
            msg = "세션이 시작되지 않았습니다."
            raise RuntimeError(msg)
        transactions: list[dict] = []
        try:
            # 거래내역 메뉴 진입
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.TextView[@text="거래내역"]',
            )
            await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.EditText[@resource-id="account_no"]',
            )
            # 계좌번호 입력
            await self._manager.find_and_input(
                self._session_id,
                '//android.widget.EditText[@resource-id="account_no"]',
                account_number,
            )
            # 기간 입력
            await self._manager.find_and_input(
                self._session_id,
                '//android.widget.EditText[@resource-id="period"]',
                period,
            )
            # 조회 실행
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.Button[@text="조회"]',
            )
            await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.ListView[@resource-id="transaction_list"]',
                timeout=20,
            )
            # 스크린샷 캡처
            await self._manager.take_screenshot(self._session_id)
            logger.info("거래내역 조회 완료: %s (기간: %s)", account_number, period)
        except Exception:
            logger.exception("거래내역 조회 실패: %s", account_number)
            if self._session_id:
                await self._manager.take_screenshot(self._session_id)

        return transactions

    async def stop(self) -> None:
        """세션 종료."""
        if self._session_id:
            try:
                await self._manager.close_session(self._session_id)
                logger.info("뱅킹 세션 종료")
            except Exception:
                logger.exception("뱅킹 세션 종료 중 오류")
            finally:
                self._session_id = None
