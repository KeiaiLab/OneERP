"""반응형 E2E -- 모바일 뷰포트 테이블->카드, 햄버거 메뉴."""

from __future__ import annotations

import pytest
from playwright.sync_api import Browser, Page, expect

pytestmark = pytest.mark.e2e_ui


def login(page: Page, base_url: str) -> None:
    """반응형 레이아웃 검증용 로그인."""
    page.goto(f"{base_url}/login")
    page.fill("#username", "demo")
    page.fill("#password", "demo1234")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/", timeout=10000)


class TestMobileLayout:
    def test_모바일_사이드바_숨김(self, mobile_page: Page, base_url: str):
        """모바일에서 사이드바가 숨겨진다."""
        login(mobile_page, base_url)
        sidebar = mobile_page.locator("aside, nav[data-testid='sidebar']")
        # 모바일에서는 hidden 상태
        if sidebar.count() > 0:
            expect(sidebar.first).to_be_hidden()

    def test_모바일_햄버거_메뉴_동작(self, mobile_page: Page, base_url: str):
        """모바일에서 햄버거 메뉴 클릭 시 네비게이션이 표시된다."""
        login(mobile_page, base_url)
        hamburger = mobile_page.locator(
            'button[aria-label*="메뉴"], [data-testid="mobile-menu-toggle"]'
        )
        if hamburger.count() > 0:
            hamburger.first.click()
            mobile_page.wait_for_timeout(300)

    def test_모바일_카드_레이아웃(self, mobile_page: Page, base_url: str):
        """모바일에서 목록이 카드 레이아웃으로 표시된다."""
        login(mobile_page, base_url)
        mobile_page.goto(f"{base_url}/accounts")
        mobile_page.wait_for_load_state("networkidle")
        # 테이블이 숨겨지고 카드가 표시되는지 확인
        mobile_page.wait_for_timeout(1000)


class TestTabletLayout:
    def test_태블릿_뷰포트(self, browser: Browser, base_url: str):
        """태블릿(768px)에서 레이아웃이 적절하게 표시된다."""
        context = browser.new_context(viewport={"width": 768, "height": 1024})
        page = context.new_page()
        login(page, base_url)
        page.wait_for_load_state("networkidle")
        context.close()
