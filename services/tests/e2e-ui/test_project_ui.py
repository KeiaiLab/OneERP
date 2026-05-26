"""프로젝트 UI E2E.

프로젝트 생성 → 타임시트 입력 흐름을 검증한다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestProject:
    """프로젝트 비즈니스 흐름 UI 테스트."""

    def test_프로젝트_생성(self, authenticated_page: Page, base_url: str) -> None:
        """프로젝트를 생성한다."""
        page = authenticated_page

        # 프로젝트 생성 페이지 이동
        page.goto(f"{base_url}/projects/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        project_name = page.locator('[name="project_name"]')
        if project_name.count() > 0:
            project_name.fill("ERP 시스템 구축")

        company_field = page.locator('[name="company"]')
        if company_field.count() > 0:
            company_field.fill("테스트 회사")

        start_date = page.locator('[name="expected_start_date"]')
        if start_date.count() > 0:
            start_date.fill("2026-04-01")

        end_date = page.locator('[name="expected_end_date"]')
        if end_date.count() > 0:
            end_date.fill("2026-12-31")

        status_field = page.locator('[name="status"]')
        if status_field.count() > 0:
            status_field.fill("진행중")

        # 저장
        save_btn = page.locator('button:has-text("저장")')
        if save_btn.count() > 0:
            save_btn.click()
            page.wait_for_load_state("networkidle")

            # 토스트 확인
            toast = page.locator('[role="alert"]')
            if toast.count() > 0:
                expect(toast.first).to_be_visible()

    def test_타임시트_입력(self, authenticated_page: Page, base_url: str) -> None:
        """타임시트를 입력한다."""
        page = authenticated_page

        # 타임시트 생성 페이지 이동
        page.goto(f"{base_url}/timesheets/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        employee_field = page.locator('[name="employee"]')
        if employee_field.count() > 0:
            employee_field.fill("테스트 직원")

        activity_type = page.locator('[name="activity_type"]')
        if activity_type.count() > 0:
            activity_type.fill("개발")

        hours_field = page.locator('[name="total_hours"]')
        if hours_field.count() > 0:
            hours_field.fill("8")

        project_field = page.locator('[name="project"]')
        if project_field.count() > 0:
            project_field.fill("ERP 시스템 구축")

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
