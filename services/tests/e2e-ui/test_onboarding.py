"""온보딩 오케스트레이터 E2E 테스트 — 초기 구축 단계, 링크, 배너 연동."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestOnboarding:
    def test_대시보드_배너에서_온보딩_링크로_이동한다(
        self, authenticated_page: Page, base_url: str
    ) -> None:
        """대시보드 배너의 온보딩 링크가 /onboarding 으로 연결된다."""
        banner = authenticated_page.locator('[data-testid="master-journey-banner"]')
        expect(banner).to_be_visible()

        onboarding_link = banner.get_by_role("link", name="/onboarding")
        expect(onboarding_link).to_have_attribute("href", "/onboarding")

        onboarding_link.click()
        authenticated_page.wait_for_url(f"{base_url}/onboarding", timeout=10000)
        expect(
            authenticated_page.get_by_role("heading", name="설치 마법사형 오케스트레이터")
        ).to_be_visible()

    def test_온보딩_페이지에_초기_구축_단계카드가_보인다(
        self, authenticated_page: Page, base_url: str
    ) -> None:
        """온보딩 페이지에 초기 구축 5단계 카드와 기존 화면 링크가 보인다."""
        page = authenticated_page
        page.goto(f"{base_url}/onboarding")
        page.wait_for_load_state("networkidle")

        expect(page.get_by_role("heading", name="설치 마법사형 오케스트레이터")).to_be_visible()
        expect(page.locator('[data-testid="onboarding-orchestrator"]')).to_be_visible()
        expect(page.get_by_role("heading", name="회사", exact=True)).to_be_visible()
        expect(page.get_by_role("heading", name="회계 기본값", exact=True)).to_be_visible()
        expect(page.get_by_role("heading", name="사용자/권한", exact=True)).to_be_visible()
        expect(page.get_by_role("heading", name="결재", exact=True)).to_be_visible()
        expect(page.get_by_role("heading", name="기초 데이터", exact=True)).to_be_visible()
        expect(
            page.locator('[data-testid="onboarding-stage-company"]').get_by_text("검증 결과")
        ).to_be_visible()
        expect(page.get_by_role("link", name="회사 화면으로 이동")).to_have_attribute(
            "href", "/companies"
        )
        expect(page.get_by_role("link", name="회계 기본값 화면으로 이동")).to_have_attribute(
            "href",
            "/accounting-periods",
        )
        expect(page.get_by_role("link", name="사용자/권한 화면으로 이동")).to_have_attribute(
            "href",
            "/users",
        )
        expect(page.get_by_role("link", name="결재 화면으로 이동")).to_have_attribute(
            "href",
            "/approval-templates",
        )
        expect(page.get_by_role("link", name="기초 데이터 화면으로 이동")).to_have_attribute(
            "href",
            "/items",
        )

    def test_온보딩_페이지에_cl1_cl5_여정이_함께_보인다(
        self, authenticated_page: Page, base_url: str
    ) -> None:
        """온보딩 페이지가 초기 구축뿐 아니라 CL1, CL5, 모듈 확장 여정도 함께 보여준다."""
        page = authenticated_page
        page.goto(f"{base_url}/onboarding")
        page.wait_for_load_state("networkidle")

        expect(
            page.locator('[data-testid="onboarding-journey-cl1"]').get_by_role(
                "heading",
                name="CL1 핵심 심화 여정",
            ),
        ).to_be_visible()
        expect(
            page.locator('[data-testid="onboarding-journey-cl5"]').get_by_role(
                "heading",
                name="CL5 핵심 심화 여정",
            ),
        ).to_be_visible()
        expect(
            page.locator('[data-testid="onboarding-journey-module_expansion"]').get_by_role(
                "heading",
                name="모듈 확장",
            ),
        ).to_be_visible()
        expect(page.get_by_role("link", name="회계 모듈 문서")).to_have_attribute(
            "href",
            "/docs/user-manual/01-accounting.md",
        )
        expect(page.get_by_role("link", name="경비→결재→회계 튜토리얼")).to_have_attribute(
            "href",
            "/docs/tutorials/03-expense-approval.md",
        )
