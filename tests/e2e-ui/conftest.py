"""Playwright E2E UI 테스트 공통 fixture.

BE 서비스 + FE Next.js 앱을 기동하고, Playwright 브라우저를 제공한다.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Generator

import pytest
from playwright.sync_api import Browser, Page

logger = logging.getLogger(__name__)

BASE_URL = os.environ.get("E2E_BASE_URL", "http://localhost:3000")

# 테스트 사용자 정보 — 환경변수로 주입 (보안)
TEST_USER = {
    "username": os.environ.get("E2E_TEST_USERNAME", "demo"),
    "password": os.environ.get("E2E_TEST_PASSWORD", "demo1234"),
}


@pytest.fixture(scope="session")
def browser_context_args() -> dict:
    """Playwright 브라우저 컨텍스트 기본 설정."""
    return {
        "viewport": {"width": 1280, "height": 720},
        "locale": "ko-KR",
        "timezone_id": "Asia/Seoul",
    }


@pytest.fixture(scope="session")
def base_url() -> str:
    """FE 앱 기본 URL."""
    return BASE_URL


@pytest.fixture
def authenticated_page(page: Page, base_url: str) -> Page:
    """로그인된 상태의 페이지를 반환한다."""
    page.goto(f"{base_url}/login")
    page.fill("#username", TEST_USER["username"])
    page.fill("#password", TEST_USER["password"])
    page.click('button[type="submit"]')
    # 대시보드로 리다이렉트 대기
    page.wait_for_url(f"{base_url}/", timeout=10000)
    return page


@pytest.fixture
def mobile_page(browser: Browser, base_url: str) -> Generator[Page]:
    """모바일 뷰포트(375x667) 페이지를 반환한다."""
    context = browser.new_context(
        viewport={"width": 375, "height": 667},
        locale="ko-KR",
    )
    _page = context.new_page()
    yield _page
    context.close()
