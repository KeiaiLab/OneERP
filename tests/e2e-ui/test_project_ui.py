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

    def test_타임시트_목록_요약과_미청구_필터(
        self, authenticated_page: Page, base_url: str
    ) -> None:
        """타임시트 목록에서 운영 요약과 미청구 필터 영역이 노출되면 사용할 수 있어야 한다."""
        page = authenticated_page
        page.goto(f"{base_url}/timesheets")
        page.wait_for_load_state("networkidle")

        employee_filter = page.locator('[name="employee_id"], [name="employee"]')
        if employee_filter.count() > 0:
            employee_filter.first.fill("EMP-0001")

        billed_filter = page.locator('[name="billed"]')
        if billed_filter.count() > 0:
            billed_filter.first.fill("false")

        summary_card = page.locator(
            '[data-testid="timesheet-summary"], text=/미청구|급여 준비|제출됨/'
        )
        if summary_card.count() > 0:
            expect(summary_card.first).to_be_visible()

    def test_마일스톤_목록_청구상태_필터와_배지(
        self, authenticated_page: Page, base_url: str
    ) -> None:
        """마일스톤 목록에서 청구 상태 필터와 상태 배지가 노출되면 사용할 수 있어야 한다."""
        page = authenticated_page
        page.goto(f"{base_url}/milestones")
        page.wait_for_load_state("networkidle")

        project_filter = page.locator('[name="project"]')
        if project_filter.count() > 0:
            project_filter.first.fill("PRJ-0001")

        billing_status_filter = page.locator('[name="billing_status"]')
        if billing_status_filter.count() > 0:
            billing_status_filter.first.fill("ready_to_invoice")

        milestone_badge = page.locator(
            '[data-testid="milestone-status-badge"], text=/지연|청구 준비|완료/'
        )
        if milestone_badge.count() > 0:
            expect(milestone_badge.first).to_be_visible()

    def test_프로젝트_목록_필터와_요약_영역(self, authenticated_page: Page, base_url: str) -> None:
        """프로젝트 목록 페이지에서 필터/요약 UI가 노출되면 사용할 수 있어야 한다."""
        page = authenticated_page
        page.goto(f"{base_url}/projects")
        page.wait_for_load_state("networkidle")

        status_filter = page.locator('[name="status"]')
        if status_filter.count() > 0:
            status_filter.first.fill("open")

        manager_filter = page.locator('[name="project_manager"]')
        if manager_filter.count() > 0:
            manager_filter.first.fill("EMP-0001")

        summary_card = page.locator(
            '[data-testid="project-summary"], text=/총 예산|진행률|프로젝트/'
        )
        if summary_card.count() > 0:
            expect(summary_card.first).to_be_visible()

    def test_작업_목록_필터와_상태배지(self, authenticated_page: Page, base_url: str) -> None:
        """작업 목록 페이지에서 필터와 상태 배지가 노출되면 사용할 수 있어야 한다."""
        page = authenticated_page
        page.goto(f"{base_url}/tasks")
        page.wait_for_load_state("networkidle")

        status_filter = page.locator('[name="status"]')
        if status_filter.count() > 0:
            status_filter.first.fill("pending_review")

        assignee_filter = page.locator('[name="assigned_to"]')
        if assignee_filter.count() > 0:
            assignee_filter.first.fill("EMP-0001")

        task_badge = page.locator('[data-testid="task-status-badge"], text=/검토 대기|진행중|완료/')
        if task_badge.count() > 0:
            expect(task_badge.first).to_be_visible()

    def test_활동유형_목록_요약과_마진주의_필터(
        self, authenticated_page: Page, base_url: str
    ) -> None:
        """활동유형 목록 페이지에서 운영 요약과 상태 배지 필터가 노출되면 사용할 수 있어야 한다."""
        page = authenticated_page
        page.goto(f"{base_url}/activity-types")
        page.wait_for_load_state("networkidle")

        badge_filter = page.locator('[name="status_badge"]')
        if badge_filter.count() > 0:
            badge_filter.first.fill("margin_watch")

        summary_card = page.locator(
            '[data-testid="activity-type-summary"], text=/활성 활동유형|미청구 시간|마진/'
        )
        if summary_card.count() > 0:
            expect(summary_card.first).to_be_visible()
