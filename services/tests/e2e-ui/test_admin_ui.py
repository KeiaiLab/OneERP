"""관리자 UI E2E -- 테넌트, 사용자, 역할, 플랜."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestAdminDashboard:
    def test_관리자_대시보드_렌더링(self, authenticated_page: Page, base_url: str):
        """관리자 페이지에 통계와 테넌트 목록이 표시된다."""
        page = authenticated_page
        page.goto(f"{base_url}/admin")
        page.wait_for_load_state("networkidle")
        expect(page.locator("h1, h2").first).to_be_visible()


class TestTenantManagement:
    def test_테넌트_목록_페이지(self, authenticated_page: Page, base_url: str):
        """테넌트 목록 페이지가 렌더링된다."""
        page = authenticated_page
        page.goto(f"{base_url}/admin/tenants")
        page.wait_for_load_state("networkidle")
        expect(page.locator("table, [data-testid='empty-state']").first).to_be_visible(
            timeout=10000
        )

    def test_테넌트_생성_폼(self, authenticated_page: Page, base_url: str):
        """테넌트 생성 폼이 렌더링된다."""
        page = authenticated_page
        page.goto(f"{base_url}/admin/tenants/new")
        page.wait_for_load_state("networkidle")
        expect(page.locator("form").first).to_be_visible(timeout=10000)


class TestUserManagement:
    def test_사용자_관리_페이지(self, authenticated_page: Page, base_url: str):
        """사용자 관리 페이지가 렌더링된다."""
        page = authenticated_page
        page.goto(f"{base_url}/admin/users")
        page.wait_for_load_state("networkidle")
        expect(page.locator("h1, h2, table").first).to_be_visible(timeout=10000)
