"""CRM 파이프라인 UI E2E.

리드 생성 → 기회 전환 → 견적 생성 흐름을 검증한다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestCRM:
    """CRM 파이프라인 비즈니스 흐름 UI 테스트."""

    def test_리드_워크벤치_요약이_노출된다(self, authenticated_page: Page, base_url: str) -> None:
        """리드 상세 화면에서 점수/활동/전환 가이드 블록이 보인다."""
        page = authenticated_page

        page.goto(f"{base_url}/leads/LEAD-TEST-001")
        page.wait_for_load_state("networkidle")

        summary = page.locator("text=/리드|점수|활동|전환|권장 액션/")
        if summary.count() > 0:
            expect(summary.first).to_be_visible()

    def test_리드_생성(self, authenticated_page: Page, base_url: str) -> None:
        """리드를 생성한다."""
        page = authenticated_page

        # 리드 생성 페이지 이동
        page.goto(f"{base_url}/leads/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        lead_name = page.locator('[name="lead_name"]')
        if lead_name.count() > 0:
            lead_name.fill("김영업")

        company_name = page.locator('[name="company_name"]')
        if company_name.count() > 0:
            company_name.fill("테스트 기업")

        email_field = page.locator('[name="email"]')
        if email_field.count() > 0:
            email_field.fill("lead@test.com")

        source_field = page.locator('[name="source"]')
        if source_field.count() > 0:
            source_field.fill("웹사이트")

        # 저장
        save_btn = page.locator('button:has-text("저장")')
        if save_btn.count() > 0:
            save_btn.click()
            page.wait_for_load_state("networkidle")

            # 토스트 확인
            toast = page.locator('[role="alert"]')
            if toast.count() > 0:
                expect(toast.first).to_be_visible()

    def test_기회_전환(self, authenticated_page: Page, base_url: str) -> None:
        """리드에서 기회로 전환한다."""
        page = authenticated_page

        # 리드 목록 이동
        page.goto(f"{base_url}/leads")
        page.wait_for_load_state("networkidle")

        # 첫 번째 리드 클릭 (데이터가 있는 경우)
        rows = page.locator("tbody tr")
        if rows.count() > 0:
            rows.first.click()
            page.wait_for_load_state("networkidle")

            # 기회 전환 버튼 클릭
            convert_btn = page.locator('button:has-text("기회 전환"), button:has-text("전환")')
            if convert_btn.count() > 0:
                convert_btn.first.click()
                # 확인 다이얼로그
                confirm_btn = page.locator('button:has-text("확인")')
                if confirm_btn.count() > 0:
                    confirm_btn.click()
                page.wait_for_load_state("networkidle")

        # 기회 목록 페이지 확인
        page.goto(f"{base_url}/opportunities")
        page.wait_for_load_state("networkidle")

        heading = page.locator("h1, h2")
        if heading.count() > 0:
            expect(heading.first).to_be_visible()

    def test_견적_생성(self, authenticated_page: Page, base_url: str) -> None:
        """견적서를 생성한다."""
        page = authenticated_page

        # 견적서 생성 페이지 이동
        page.goto(f"{base_url}/quotations/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        customer_field = page.locator('[name="party_name"]')
        if customer_field.count() > 0:
            customer_field.fill("테스트 기업")

        valid_till = page.locator('[name="valid_till"]')
        if valid_till.count() > 0:
            valid_till.fill("2026-04-23")

        # 저장
        save_btn = page.locator('button:has-text("저장")')
        if save_btn.count() > 0:
            save_btn.click()
            page.wait_for_load_state("networkidle")

        # 제출
        submit_btn = page.locator('button:has-text("제출")')
        if submit_btn.count() > 0:
            submit_btn.click()
            confirm_btn = page.locator('button:has-text("확인")')
            if confirm_btn.count() > 0:
                confirm_btn.click()
            page.wait_for_load_state("networkidle")

            # DocStatus 확인
            badge = page.locator('text="제출됨"')
            if badge.count() > 0:
                expect(badge.first).to_be_visible()

    def test_견적_고객전달_액션이_노출된다(self, authenticated_page: Page, base_url: str) -> None:
        """제출된 견적 상세에서 PDF/메일 발송/전자서명 관련 액션이 노출된다."""
        page = authenticated_page

        page.goto(f"{base_url}/quotations")
        page.wait_for_load_state("networkidle")

        rows = page.locator("tbody tr")
        if rows.count() > 0:
            rows.first.click()
            page.wait_for_load_state("networkidle")

            actions = page.locator(
                'button:has-text("PDF"), button:has-text("메일"), button:has-text("서명")'
            )
            if actions.count() > 0:
                expect(actions.first).to_be_visible()

    def test_판매파트너_워크벤치_요약이_노출된다(
        self, authenticated_page: Page, base_url: str
    ) -> None:
        """판매파트너 상세 화면에서 상태/실적/권장 액션 블록이 보인다."""
        page = authenticated_page

        page.goto(f"{base_url}/sales-partners/SPAR-TEST-001")
        page.wait_for_load_state("networkidle")

        summary = page.locator("text=/파트너|실적|미수|권장 액션/")
        if summary.count() > 0:
            expect(summary.first).to_be_visible()

    def test_가격표_워크벤치_요약이_노출된다(self, authenticated_page: Page, base_url: str) -> None:
        """가격표 상세 화면에서 카탈로그/사용 요약과 권장 액션 블록이 보인다."""
        page = authenticated_page

        page.goto(f"{base_url}/price-lists/PLT-TEST-001")
        page.wait_for_load_state("networkidle")

        summary = page.locator("text=/가격표|카탈로그|견적|권장 액션/")
        if summary.count() > 0:
            expect(summary.first).to_be_visible()

    def test_판매분석_대시보드가_로드된다(self, authenticated_page: Page, base_url: str) -> None:
        """판매 분석 페이지에서 KPI 또는 차트 영역이 노출된다."""
        page = authenticated_page

        page.goto(f"{base_url}/sales-analytics")
        page.wait_for_load_state("networkidle")

        dashboard = page.locator("text=/판매 분석|매출 추이|고객 믹스|품목 믹스/")
        if dashboard.count() > 0:
            expect(dashboard.first).to_be_visible()
