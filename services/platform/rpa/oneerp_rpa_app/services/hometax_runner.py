"""홈택스 앱 자동화 — 전자세금계산서 발급/조회.

홈택스 모바일 앱(kr.go.nts.hometax)에 대한 Appium 기반
자동화를 수행한다. 공동인증서 로그인, 세금계산서 발급/조회를 지원한다.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .appium_manager import AppiumManager

logger = logging.getLogger(__name__)


class HometaxRunner:
    """홈택스 앱 자동화 — 전자세금계산서 발급/조회."""

    PACKAGE = "kr.go.nts.hometax"
    ACTIVITY = ".MainActivity"

    def __init__(self, appium_manager: AppiumManager) -> None:
        self._manager = appium_manager
        self._session_id: str | None = None

    async def start(self, device_id: str) -> None:
        """홈택스 앱 세션 시작."""
        try:
            self._session_id = await self._manager.create_android_session(
                device_id=device_id,
                app_package=self.PACKAGE,
                app_activity=self.ACTIVITY,
            )
            logger.info("홈택스 앱 세션 시작 (기기: %s)", device_id)
        except Exception:
            logger.exception("홈택스 앱 시작 실패 (기기: %s)", device_id)
            raise

    async def login(self, cert_password: str) -> bool:
        """공동인증서로 로그인. 인증서는 기기에 미리 설치되어 있어야 함."""
        if self._session_id is None:
            msg = "세션이 시작되지 않았습니다. start()를 먼저 호출하세요."
            raise RuntimeError(msg)
        try:
            # 로그인 버튼 클릭
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.Button[@text="로그인"]',
            )
            # 공동인증서 로그인 메뉴 선택
            await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.TextView[@text="공동인증서"]',
            )
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.TextView[@text="공동인증서"]',
            )
            # 인증서 비밀번호 입력
            await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.EditText[@resource-id="password"]',
                timeout=15,
            )
            await self._manager.find_and_input(
                self._session_id,
                '//android.widget.EditText[@resource-id="password"]',
                cert_password,
            )
            # 확인 버튼 클릭
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.Button[@text="확인"]',
            )
            # 로그인 완료 대기
            logged_in = await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.TextView[@text="마이홈택스"]',
                timeout=20,
            )
            if logged_in:
                logger.info("홈택스 로그인 성공")
                # 로그인 성공 스크린샷
                await self._manager.take_screenshot(self._session_id)
            return logged_in
        except Exception:
            logger.exception("홈택스 로그인 실패")
            if self._session_id:
                await self._manager.take_screenshot(self._session_id)
            return False

    async def issue_tax_invoice(self, invoice_data: dict) -> dict:
        """전자세금계산서 발급.

        단계: 메뉴→전자세금계산서→발급→공급자정보→공급받는자정보→품목→발급
        """
        if self._session_id is None:
            msg = "세션이 시작되지 않았습니다."
            raise RuntimeError(msg)
        result: dict = {"success": False, "invoice_number": "", "screenshots": []}
        try:
            # 1단계: 전자세금계산서 메뉴 진입
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.TextView[@text="전자세금계산서"]',
            )
            screenshot = await self._manager.take_screenshot(self._session_id)
            result["screenshots"].append(len(screenshot))

            # 2단계: 발급 메뉴 선택
            await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.TextView[@text="발급하기"]',
            )
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.TextView[@text="발급하기"]',
            )

            # 3단계: 공급자 정보 입력
            supplier = invoice_data.get("supplier", {})
            if supplier.get("business_number"):
                await self._manager.find_and_input(
                    self._session_id,
                    '//android.widget.EditText[@resource-id="supplier_biz_no"]',
                    supplier["business_number"],
                )

            # 4단계: 공급받는자 정보 입력
            buyer = invoice_data.get("buyer", {})
            if buyer.get("business_number"):
                await self._manager.find_and_input(
                    self._session_id,
                    '//android.widget.EditText[@resource-id="buyer_biz_no"]',
                    buyer["business_number"],
                )

            # 5단계: 품목 정보 입력
            for item in invoice_data.get("items", []):
                if item.get("name"):
                    await self._manager.find_and_input(
                        self._session_id,
                        '//android.widget.EditText[@resource-id="item_name"]',
                        item["name"],
                    )
                if item.get("amount"):
                    await self._manager.find_and_input(
                        self._session_id,
                        '//android.widget.EditText[@resource-id="item_amount"]',
                        str(item["amount"]),
                    )

            # 6단계: 발급 버튼 클릭
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.Button[@text="발급"]',
            )

            # 발급 완료 확인
            issued = await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.TextView[contains(@text, "발급완료")]',
                timeout=30,
            )
            if issued:
                result["success"] = True
                logger.info("전자세금계산서 발급 성공")

            screenshot = await self._manager.take_screenshot(self._session_id)
            result["screenshots"].append(len(screenshot))

        except Exception:
            logger.exception("전자세금계산서 발급 실패")
            if self._session_id:
                await self._manager.take_screenshot(self._session_id)

        return result

    async def query_tax_invoices(self, period: str) -> list[dict]:
        """기간별 세금계산서 조회."""
        if self._session_id is None:
            msg = "세션이 시작되지 않았습니다."
            raise RuntimeError(msg)
        invoices: list[dict] = []
        try:
            # 조회 메뉴 진입
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.TextView[@text="전자세금계산서"]',
            )
            await self._manager.wait_for_element(
                self._session_id,
                '//android.widget.TextView[@text="조회하기"]',
            )
            await self._manager.find_and_click(
                self._session_id,
                '//android.widget.TextView[@text="조회하기"]',
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
                '//android.widget.ListView[@resource-id="invoice_list"]',
                timeout=20,
            )
            # 스크린샷으로 결과 기록
            await self._manager.take_screenshot(self._session_id)
            logger.info("세금계산서 조회 완료 (기간: %s)", period)
        except Exception:
            logger.exception("세금계산서 조회 실패 (기간: %s)", period)
            if self._session_id:
                await self._manager.take_screenshot(self._session_id)

        return invoices

    async def stop(self) -> None:
        """세션 종료."""
        if self._session_id:
            try:
                await self._manager.close_session(self._session_id)
                logger.info("홈택스 세션 종료")
            except Exception:
                logger.exception("홈택스 세션 종료 중 오류")
            finally:
                self._session_id = None
