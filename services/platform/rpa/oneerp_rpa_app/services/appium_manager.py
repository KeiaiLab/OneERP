"""Appium 서버 + 모바일 기기 세션 관리.

Android 기기에 대한 Appium 세션 생성·종료, 요소 탐색·클릭·입력,
스크린샷 캡처 등 공통 자동화 오퍼레이션을 제공한다.
"""

from __future__ import annotations

import logging
import subprocess
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

logger = logging.getLogger(__name__)


class AppiumManager:
    """Appium 서버 + 모바일 기기 세션 관리."""

    def __init__(self, appium_url: str = "http://localhost:4723") -> None:
        self._appium_url = appium_url
        self._active_sessions: dict[str, WebDriver] = {}

    async def create_android_session(
        self,
        device_id: str,
        app_package: str,
        app_activity: str,
    ) -> str:
        """Android 기기에 Appium 세션 생성. 세션 ID 반환."""
        try:
            from appium import webdriver as appium_webdriver
            from appium.options.android import UiAutomator2Options

            options = UiAutomator2Options()
            options.platform_name = "Android"
            options.udid = device_id
            options.app_package = app_package
            options.app_activity = app_activity
            options.no_reset = True
            options.auto_grant_permissions = True

            driver = appium_webdriver.Remote(
                command_executor=self._appium_url,
                options=options,
            )
            session_id = cast("str", driver.session_id)
            self._active_sessions[session_id] = driver
            logger.info("Appium 세션 생성 완료: %s (기기: %s)", session_id, device_id)
            return session_id
        except Exception:
            logger.exception("Appium 세션 생성 실패 (기기: %s)", device_id)
            raise

    async def close_session(self, session_id: str) -> None:
        """세션 종료."""
        driver = self._active_sessions.pop(session_id, None)
        if driver is None:
            logger.warning("종료할 세션을 찾을 수 없음: %s", session_id)
            return
        try:
            driver.quit()
            logger.info("Appium 세션 종료: %s", session_id)
        except Exception:
            logger.exception("Appium 세션 종료 중 오류: %s", session_id)

    def get_connected_devices(self) -> list[dict]:
        """ADB를 통해 연결된 Android 기기 목록 반환."""
        try:
            result = subprocess.run(
                ["/usr/bin/adb", "devices", "-l"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            devices: list[dict] = []
            for line in result.stdout.strip().splitlines()[1:]:
                parts = line.split()
                if len(parts) >= 2 and parts[1] == "device":
                    device_info: dict[str, str] = {"id": parts[0], "status": "connected"}
                    # 추가 속성 파싱 (model, product 등)
                    for part in parts[2:]:
                        if ":" in part:
                            key, value = part.split(":", 1)
                            device_info[key] = value
                    devices.append(device_info)
            return devices
        except FileNotFoundError:
            logger.warning("ADB가 설치되지 않았거나 PATH에 없습니다")
            return []
        except subprocess.TimeoutExpired:
            logger.warning("ADB 기기 목록 조회 시간 초과")
            return []

    async def take_screenshot(self, session_id: str) -> bytes:
        """현재 화면 스크린샷 캡처."""
        driver = self._active_sessions.get(session_id)
        if driver is None:
            msg = f"세션을 찾을 수 없음: {session_id}"
            raise ValueError(msg)
        try:
            return driver.get_screenshot_as_png()
        except Exception:
            logger.exception("스크린샷 캡처 실패: %s", session_id)
            raise

    async def find_and_click(
        self,
        session_id: str,
        selector: str,
        by: str = "xpath",
    ) -> bool:
        """요소 찾아서 클릭."""
        driver = self._active_sessions.get(session_id)
        if driver is None:
            msg = f"세션을 찾을 수 없음: {session_id}"
            raise ValueError(msg)
        try:
            from appium.webdriver.common.appiumby import AppiumBy

            by_method = getattr(AppiumBy, by.upper(), AppiumBy.XPATH)
            element = driver.find_element(by_method, selector)
            element.click()
            return True
        except Exception:
            logger.exception("요소 클릭 실패: %s (selector=%s)", session_id, selector)
            return False

    async def find_and_input(
        self,
        session_id: str,
        selector: str,
        text: str,
        by: str = "xpath",
    ) -> bool:
        """요소 찾아서 텍스트 입력."""
        driver = self._active_sessions.get(session_id)
        if driver is None:
            msg = f"세션을 찾을 수 없음: {session_id}"
            raise ValueError(msg)
        try:
            from appium.webdriver.common.appiumby import AppiumBy

            by_method = getattr(AppiumBy, by.upper(), AppiumBy.XPATH)
            element = driver.find_element(by_method, selector)
            element.clear()
            element.send_keys(text)
            return True
        except Exception:
            logger.exception("텍스트 입력 실패: %s (selector=%s)", session_id, selector)
            return False

    async def wait_for_element(
        self,
        session_id: str,
        selector: str,
        timeout: int = 10,
        by: str = "xpath",
    ) -> bool:
        """요소가 나타날 때까지 대기."""
        driver = self._active_sessions.get(session_id)
        if driver is None:
            msg = f"세션을 찾을 수 없음: {session_id}"
            raise ValueError(msg)
        try:
            from appium.webdriver.common.appiumby import AppiumBy
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.support.ui import WebDriverWait

            by_method = getattr(AppiumBy, by.upper(), AppiumBy.XPATH)
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by_method, selector)),
            )
            return True
        except Exception:
            logger.warning(
                "요소 대기 시간 초과: %s (selector=%s, timeout=%d)",
                session_id,
                selector,
                timeout,
            )
            return False
