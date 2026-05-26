"""인증 E2E 테스트 — 로그인/로그아웃/미인증 리다이렉트."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestLogin:
    def test_로그인_페이지_렌더링(self, page: Page, base_url: str):
        """로그인 페이지에 username/password 입력필드와 로그인 버튼이 표시된다."""
        page.goto(f"{base_url}/login")
        expect(page.locator("#username")).to_be_visible()
        expect(page.locator("#password")).to_be_visible()
        expect(page.locator('button:has-text("로그인")')).to_be_visible()

    def test_로그인_성공_대시보드_리다이렉트(self, page: Page, base_url: str):
        """올바른 자격증명으로 로그인하면 대시보드로 리다이렉트된다."""
        page.goto(f"{base_url}/login")
        page.fill("#username", "demo")
        page.fill("#password", "demo1234")
        page.click('button:has-text("로그인")')
        page.wait_for_url(f"{base_url}/", timeout=10000)
        expect(page).to_have_url(f"{base_url}/")

    def test_로그인_실패_에러_메시지(self, page: Page, base_url: str):
        """잘못된 자격증명은 에러 메시지를 표시한다."""
        page.goto(f"{base_url}/login")
        page.fill("#username", "wrong")
        page.fill("#password", "wrong")
        page.click('button:has-text("로그인")')
        # 에러 메시지 확인
        expect(page.locator('[role="alert"], .text-danger, .error')).to_be_visible(timeout=5000)

    def test_미인증_접근_로그인_리다이렉트(self, page: Page, base_url: str):
        """인증 없이 보호된 페이지 접근 시 로그인으로 리다이렉트된다."""
        page.goto(f"{base_url}/accounts")
        # 로그인 페이지로 리다이렉트 확인
        page.wait_for_url("**login**", timeout=10000)
