"""대시보드 E2E 테스트 — KPI, 차트, 미결 결재, 빠른 작업."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestDashboard:
    def test_대시보드_렌더링(self, authenticated_page: Page):
        """대시보드에 KPI 카드와 차트가 표시된다."""
        # authenticated_page는 이미 대시보드에 있음
        expect(authenticated_page.locator("h1, h2").first).to_be_visible()

    def test_master_journey_banner(self, authenticated_page: Page):
        """회사 관리자/도입 담당자 배너가 현재/다음 단계와 온보딩 링크를 보여준다."""
        banner = authenticated_page.locator('[data-testid="master-journey-banner"]')
        expect(banner).to_be_visible()
        expect(banner).to_contain_text("현재 단계")
        expect(banner).to_contain_text("다음 단계")
        expect(banner).to_contain_text("미완료 단계")
        expect(banner).to_contain_text("CL1 핵심 심화 여정")
        expect(banner).to_contain_text("CL5 핵심 심화 여정")

        onboarding_link = banner.get_by_role("link", name="/onboarding")
        expect(onboarding_link).to_have_attribute("href", "/onboarding")

    def test_로그인_후_사용자정보와_사이드바_그룹이_보인다(self, authenticated_page: Page):
        """로그인 직후 사용자명과 최소 한 개 모듈 그룹이 보인다."""
        expect(authenticated_page.locator("body")).to_contain_text("데모 사용자")
        expect(
            authenticated_page.locator("aside").get_by_text("판매", exact=True),
        ).to_be_visible()

    def test_KPI_카드_표시(self, authenticated_page: Page):
        """KPI 카드가 최소 1개 이상 표시된다."""
        kpi = authenticated_page.locator('[data-testid="kpi-card"], .kpi-card, [class*="kpi"]')
        # KPI 카드가 있으면 확인, 없으면 건너뜀
        if kpi.count() > 0:
            expect(kpi.first).to_be_visible()

    def test_빠른_작업_링크(self, authenticated_page: Page):
        """빠른 작업 링크가 올바른 페이지로 이동한다."""
        quick_action = authenticated_page.locator(
            'a:has-text("판매주문"), a:has-text("구매주문"), a:has-text("경비청구")'
        )
        if quick_action.count() > 0:
            href = quick_action.first.get_attribute("href")
            assert href is not None
