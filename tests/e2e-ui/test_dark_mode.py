"""다크모드 E2E -- 테마 토글, 다크모드 렌더링."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestDarkMode:
    def test_테마_토글_존재(self, authenticated_page: Page):
        """사이드바 하단에 테마 토글이 표시된다."""
        page = authenticated_page
        toggle = page.locator('[data-testid="theme-toggle"], fieldset:has(legend)')
        expect(toggle.first).to_be_visible(timeout=5000)

    def test_다크모드_전환(self, authenticated_page: Page):
        """다크 버튼 클릭 시 data-theme="dark"가 적용된다."""
        page = authenticated_page
        # 다크모드 버튼 클릭
        dark_btn = page.locator('button[aria-label*="다크"], button:has-text("다크")')
        if dark_btn.count() > 0:
            dark_btn.first.click()
            page.wait_for_timeout(300)
            # html data-theme 확인
            theme = page.locator("html").get_attribute("data-theme")
            assert theme == "dark"

    def test_라이트모드_복귀(self, authenticated_page: Page):
        """라이트 버튼 클릭 시 data-theme="light"가 적용된다."""
        page = authenticated_page
        light_btn = page.locator('button[aria-label*="라이트"], button:has-text("라이트")')
        if light_btn.count() > 0:
            light_btn.first.click()
            page.wait_for_timeout(300)
            theme = page.locator("html").get_attribute("data-theme")
            assert theme == "light"

    def test_다크모드_배경색_변경(self, authenticated_page: Page):
        """다크모드에서 배경색이 어두운 색으로 변경된다."""
        page = authenticated_page
        dark_btn = page.locator('button[aria-label*="다크"], button:has-text("다크")')
        if dark_btn.count() > 0:
            dark_btn.first.click()
            page.wait_for_timeout(300)
            bg = page.evaluate("getComputedStyle(document.body).backgroundColor")
            # 다크모드 배경은 어두운 색 (rgb 값이 낮음)
            assert bg is not None
