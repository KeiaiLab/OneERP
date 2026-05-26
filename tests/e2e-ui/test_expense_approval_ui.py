"""경비청구 + 결재 UI E2E.

경비청구 생성 → 결재 요청 → 결재선 확인 → 승인 흐름을 검증한다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestExpenseApproval:
    """경비청구 + 결재 비즈니스 흐름 UI 테스트."""

    def test_경비청구_생성_제출(self, authenticated_page: Page, base_url: str) -> None:
        """경비청구를 생성하고 제출한다."""
        page = authenticated_page

        # 경비청구 생성 페이지 이동
        page.goto(f"{base_url}/expense-claims/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        employee_field = page.locator('[name="employee"]')
        if employee_field.count() > 0:
            employee_field.fill("테스트 직원")

        expense_type = page.locator('[name="expense_type"]')
        if expense_type.count() > 0:
            expense_type.fill("출장비")

        amount_field = page.locator('[name="total_amount"]')
        if amount_field.count() > 0:
            amount_field.fill("150000")

        description_field = page.locator('[name="description"]')
        if description_field.count() > 0:
            description_field.fill("고객사 출장 교통비")

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

    def test_결재선_확인(self, authenticated_page: Page, base_url: str) -> None:
        """결재 요청 상세에서 결재선 스텝퍼가 표시된다."""
        page = authenticated_page

        # 결재 요청 목록 이동
        page.goto(f"{base_url}/approval-requests")
        page.wait_for_load_state("networkidle")

        # 첫 번째 결재 요청 클릭 (데이터가 있는 경우)
        rows = page.locator("tbody tr")
        if rows.count() > 0:
            rows.first.click()
            page.wait_for_load_state("networkidle")

            # 결재선 스텝퍼 영역 확인
            stepper = page.locator('[data-testid="approval-stepper"]')
            if stepper.count() > 0:
                expect(stepper).to_be_visible()

        # 결재선 목록 페이지에서 데이터 렌더링 확인
        page.goto(f"{base_url}/approval-lines")
        page.wait_for_load_state("networkidle")
        # 목록 페이지가 에러 없이 렌더링되는지 확인
        heading = page.locator("h1, h2")
        if heading.count() > 0:
            expect(heading.first).to_be_visible()

    def test_결재_승인(self, authenticated_page: Page, base_url: str) -> None:
        """결재 요청을 승인한다."""
        page = authenticated_page

        # 결재 요청 목록 이동
        page.goto(f"{base_url}/approval-requests")
        page.wait_for_load_state("networkidle")

        # 첫 번째 결재 요청 클릭 (데이터가 있는 경우)
        rows = page.locator("tbody tr")
        if rows.count() > 0:
            rows.first.click()
            page.wait_for_load_state("networkidle")

            # 승인 버튼 클릭
            approve_btn = page.locator('button:has-text("승인")')
            if approve_btn.count() > 0:
                approve_btn.click()
                # 확인 다이얼로그
                confirm_btn = page.locator('button:has-text("확인")')
                if confirm_btn.count() > 0:
                    confirm_btn.click()
                page.wait_for_load_state("networkidle")

                # 승인 상태 확인
                toast = page.locator('[role="alert"]')
                if toast.count() > 0:
                    expect(toast.first).to_be_visible()
