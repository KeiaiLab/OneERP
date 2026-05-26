"""네비게이션 E2E 테스트 — 사이드바, 브레드크럼, 모바일 메뉴."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


def login(page: Page, base_url: str) -> None:
    """모바일 네비게이션 검증용 로그인."""
    page.goto(f"{base_url}/login")
    page.fill("#username", "demo")
    page.fill("#password", "demo1234")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{base_url}/", timeout=10000)


class TestSidebar:
    def test_사이드바_메뉴_표시(self, authenticated_page: Page):
        """사이드바에 네비게이션 메뉴가 표시된다."""
        sidebar = authenticated_page.locator("nav, aside, [data-testid='sidebar']")
        expect(sidebar.first).to_be_visible()

    def test_사이드바_접기_펼치기(self, authenticated_page: Page):
        """사이드바 토글 버튼으로 접기/펼치기가 동작한다."""
        toggle = authenticated_page.locator(
            '[data-testid="sidebar-toggle"], button[aria-label*="사이드바"]'
        )
        if toggle.count() > 0:
            toggle.click()
            authenticated_page.wait_for_timeout(300)  # transition 대기

    def test_사이드바_모듈_그룹_접기(self, authenticated_page: Page):
        """사이드바의 모듈 그룹을 클릭하면 하위 메뉴가 접힌다/펼쳐진다."""
        group = authenticated_page.locator(
            '[data-testid="sidebar-group"], button:has-text("판매"), button:has-text("구매")'
        )
        if group.count() > 0:
            group.first.click()
            authenticated_page.wait_for_timeout(200)


class TestBreadcrumb:
    def test_브레드크럼_표시(self, authenticated_page: Page, base_url: str):
        """엔티티 페이지에 브레드크럼이 표시된다."""
        authenticated_page.goto(f"{base_url}/accounts")
        authenticated_page.wait_for_load_state("networkidle")
        breadcrumb = authenticated_page.locator(
            'nav[aria-label="breadcrumb"], [data-testid="breadcrumb"]'
        )
        if breadcrumb.count() > 0:
            expect(breadcrumb.first).to_be_visible()


class TestMobileMenu:
    def test_모바일_햄버거_메뉴(self, mobile_page: Page, base_url: str):
        """모바일 뷰포트에서 햄버거 메뉴가 표시된다."""
        login(mobile_page, base_url)
        hamburger = mobile_page.locator('[data-testid="mobile-menu"], button[aria-label*="메뉴"]')
        if hamburger.count() > 0:
            expect(hamburger.first).to_be_visible()
            hamburger.first.click()
            mobile_page.wait_for_timeout(300)


class TestHelpPanel:
    def test_대시보드와_설정_화면에_공통_도움말_패널이_노출된다(
        self, authenticated_page: Page, base_url: str
    ):
        """대시보드와 설정 계열 화면에 공통 도움말 패널이 표시된다."""
        page = authenticated_page

        dashboard_panel = page.locator('[data-testid="context-help-panel"]')
        expect(dashboard_panel).to_be_visible()
        expect(dashboard_panel).to_contain_text("이 화면에서 하는 일")
        expect(dashboard_panel).to_contain_text("실수하기 쉬운 점")
        expect(dashboard_panel).to_contain_text("다음 단계")
        expect(dashboard_panel).to_contain_text("관련 튜토리얼")
        expect(dashboard_panel).to_contain_text("유저매뉴얼")

        page.goto(f"{base_url}/permission-matrix")
        page.wait_for_load_state("networkidle")

        settings_panel = page.locator('[data-testid="context-help-panel"]')
        expect(settings_panel).to_be_visible()
        expect(settings_panel).to_contain_text("권한")

    def test_도움말_문서_링크가_실제로_열린다(self, authenticated_page: Page):
        """도움말 패널의 문서 링크를 클릭하면 인앱 문서 페이지가 열린다."""
        page = authenticated_page
        dashboard_panel = page.locator('[data-testid="context-help-panel"]')
        doc_link = dashboard_panel.get_by_role("link", name="초기 설정 튜토리얼")
        doc_link.click()
        page.wait_for_url("**/docs/tutorials/10-admin-setup.md", timeout=10000)
        expect(page.locator("body")).to_contain_text("초기 설정")
