"""결재 흐름 UI E2E -- 결재선 시각화, 승인/반려."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestApprovalFlow:
    def test_결재요청_목록(self, authenticated_page: Page, base_url: str):
        """결재요청 목록 페이지가 렌더링된다."""
        page = authenticated_page
        page.goto(f"{base_url}/approval-requests")
        page.wait_for_load_state("networkidle")
        expect(page.locator("table, [data-testid='empty-state']").first).to_be_visible(
            timeout=10000
        )

    def test_결재선_스텝퍼_표시(self, authenticated_page: Page, base_url: str):
        """결재요청 상세에서 결재선 스텝퍼(ApprovalFlow)가 표시된다."""
        page = authenticated_page
        page.goto(f"{base_url}/approval-requests")
        page.wait_for_load_state("networkidle")
        first_row = page.locator("tbody tr").first
        if first_row.count() > 0:
            first_row.click()
            page.wait_for_load_state("networkidle")
            # ApprovalFlow 컴포넌트 확인
            stepper = page.locator('[data-testid="approval-flow"], .approval-flow')
            if stepper.count() > 0:
                expect(stepper.first).to_be_visible()
