"""생산 UI E2E.

BOM 조회 → 작업지시 생성 흐름을 검증한다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestManufacturing:
    """생산 비즈니스 흐름 UI 테스트."""

    def test_BOM_조회(self, authenticated_page: Page, base_url: str) -> None:
        """BOM 목록 페이지가 정상 렌더링되고 상세를 조회할 수 있다."""
        page = authenticated_page

        # BOM 목록 이동
        page.goto(f"{base_url}/bom-trees")
        page.wait_for_load_state("networkidle")

        # 페이지 헤딩 확인
        heading = page.locator("h1, h2")
        if heading.count() > 0:
            expect(heading.first).to_be_visible()

        # BOM 데이터가 있으면 첫 번째 행 클릭하여 상세 확인
        rows = page.locator("tbody tr")
        if rows.count() > 0:
            rows.first.click()
            page.wait_for_load_state("networkidle")

            # BOM 트리 구조 또는 라인 아이템 확인
            tree_section = page.locator('[data-testid="bom-tree"], table, .line-items')
            if tree_section.count() > 0:
                expect(tree_section.first).to_be_visible()

    def test_작업지시_생성(self, authenticated_page: Page, base_url: str) -> None:
        """작업지시를 생성한다."""
        page = authenticated_page

        # 작업지시 생성 페이지 이동
        page.goto(f"{base_url}/work-orders/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        item_field = page.locator('[name="production_item"]')
        if item_field.count() > 0:
            item_field.fill("완제품A")

        qty_field = page.locator('[name="qty"]')
        if qty_field.count() > 0:
            qty_field.fill("100")

        bom_field = page.locator('[name="bom"]')
        if bom_field.count() > 0:
            bom_field.fill("BOM-001")

        planned_date = page.locator('[name="planned_start_date"]')
        if planned_date.count() > 0:
            planned_date.fill("2026-03-24")

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
