"""Stock UI E2E - 품목 워크벤치 페이지 로딩 검증."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestStockUi:
    def test_품목_워크벤치_페이지가_로드된다(self, authenticated_page: Page, base_url: str) -> None:
        """품목 페이지가 로드되고 워크벤치 핵심 영역을 노출한다."""
        page = authenticated_page
        page.goto(f"{base_url}/items")
        page.wait_for_load_state("networkidle")

        heading_or_table = page.locator(
            'text="품목", text="Item", [data-testid="item-workbench"], table, form'
        )
        expect(heading_or_table.first).to_be_visible(timeout=10000)

        group_filter = page.locator(
            '[name="item_group"], select[name="item_group"], [data-testid="item-group-filter"]'
        )
        if group_filter.count() > 0:
            expect(group_filter.first).to_be_visible()
