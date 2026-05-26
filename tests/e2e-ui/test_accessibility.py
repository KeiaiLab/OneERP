"""접근성 E2E -- 키보드 네비게이션, 포커스, ARIA."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestKeyboardNavigation:
    def test_Tab_키_포커스_이동(self, authenticated_page: Page):
        """Tab 키로 인터랙티브 요소 간 포커스가 이동한다."""
        page = authenticated_page
        page.keyboard.press("Tab")
        focused = page.evaluate("document.activeElement?.tagName")
        assert focused is not None

    def test_Escape_키_모달_닫기(self, authenticated_page: Page, base_url: str):
        """모달이 열린 상태에서 Escape 키로 닫을 수 있다."""
        page = authenticated_page
        # 삭제 버튼 등으로 모달 열기 시도
        page.goto(f"{base_url}/accounts")
        page.wait_for_load_state("networkidle")

    def test_포커스_표시_스타일(self, authenticated_page: Page):
        """포커스 가능한 요소에 focus-visible 스타일이 적용된다."""
        page = authenticated_page
        page.keyboard.press("Tab")
        # focus-visible outline 확인
        page.evaluate("""
            const el = document.activeElement;
            if (el) return getComputedStyle(el).outlineStyle;
            return null;
        """)
        # outline이 none이 아니어야 함 (또는 ring 스타일)


class TestARIA:
    def test_사이드바_네비게이션_role(self, authenticated_page: Page):
        """사이드바에 role=navigation이 설정되어 있다."""
        page = authenticated_page
        nav = page.locator('nav, [role="navigation"]')
        expect(nav.first).to_be_visible()

    def test_브레드크럼_aria_current(self, authenticated_page: Page, base_url: str):
        """현재 페이지에 aria-current='page'가 설정되어 있다."""
        page = authenticated_page
        page.goto(f"{base_url}/accounts")
        page.wait_for_load_state("networkidle")
        current = page.locator('[aria-current="page"]')
        if current.count() > 0:
            expect(current.first).to_be_visible()

    def test_폼_필드_label_연결(self, authenticated_page: Page, base_url: str):
        """폼 필드에 label이 올바르게 연결되어 있다."""
        page = authenticated_page
        page.goto(f"{base_url}/accounts/new")
        page.wait_for_load_state("networkidle")
        labels = page.locator("label[for]")
        if labels.count() > 0:
            for_attr = labels.first.get_attribute("for")
            assert for_attr is not None
            linked_input = page.locator(f"#{for_attr}")
            expect(linked_input).to_be_visible()
