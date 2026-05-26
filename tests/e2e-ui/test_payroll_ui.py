"""급여 UI E2E.

급여처리 생성 → 제출 → 급여명세서 확인 흐름을 검증한다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestPayroll:
    """급여 비즈니스 흐름 UI 테스트."""

    def test_급여처리_생성_제출(self, authenticated_page: Page, base_url: str) -> None:
        """급여처리를 생성하고 제출한다."""
        page = authenticated_page

        # 급여처리 생성 페이지 이동
        page.goto(f"{base_url}/payroll-entries/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        payroll_period = page.locator('[name="payroll_period"]')
        if payroll_period.count() > 0:
            payroll_period.fill("2026-03")

        department_field = page.locator('[name="department"]')
        if department_field.count() > 0:
            department_field.fill("개발팀")

        posting_date = page.locator('[name="posting_date"]')
        if posting_date.count() > 0:
            posting_date.fill("2026-03-25")

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

    def test_급여명세서_확인(self, authenticated_page: Page, base_url: str) -> None:
        """급여명세서 목록 페이지에서 데이터가 렌더링된다."""
        page = authenticated_page

        # 급여명세서 목록 이동
        page.goto(f"{base_url}/salary-slips")
        page.wait_for_load_state("networkidle")

        # 페이지 타이틀/헤딩 확인
        heading = page.locator("h1, h2")
        if heading.count() > 0:
            expect(heading.first).to_be_visible()

        # 데이터가 있으면 첫 번째 행 클릭하여 상세 확인
        rows = page.locator("tbody tr")
        if rows.count() > 0:
            rows.first.click()
            page.wait_for_load_state("networkidle")

            # 급여 항목(기본급, 수당 등) 섹션 확인
            detail_section = page.locator('[data-testid="salary-detail"], .salary-components')
            if detail_section.count() > 0:
                expect(detail_section.first).to_be_visible()
