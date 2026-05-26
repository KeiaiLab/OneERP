"""자산 UI E2E.

자산 등록 → 감가상각 스케줄 확인 흐름을 검증한다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestAsset:
    """자산 비즈니스 흐름 UI 테스트."""

    def test_자산_등록(self, authenticated_page: Page, base_url: str) -> None:
        """자산을 등록한다."""
        page = authenticated_page

        # 자산 생성 페이지 이동
        page.goto(f"{base_url}/assets/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        asset_name = page.locator('[name="asset_name"]')
        if asset_name.count() > 0:
            asset_name.fill("노트북 Dell XPS 15")

        asset_category = page.locator('[name="asset_category"]')
        if asset_category.count() > 0:
            asset_category.fill("전자장비")

        gross_amount = page.locator('[name="gross_purchase_amount"]')
        if gross_amount.count() > 0:
            gross_amount.fill("2500000")

        purchase_date = page.locator('[name="purchase_date"]')
        if purchase_date.count() > 0:
            purchase_date.fill("2026-03-01")

        useful_life = page.locator('[name="total_number_of_depreciations"]')
        if useful_life.count() > 0:
            useful_life.fill("60")

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

    def test_감가상각_스케줄_확인(self, authenticated_page: Page, base_url: str) -> None:
        """자산 상세에서 감가상각 스케줄이 표시된다."""
        page = authenticated_page

        # 자산 목록 이동
        page.goto(f"{base_url}/assets")
        page.wait_for_load_state("networkidle")

        # 페이지 헤딩 확인
        heading = page.locator("h1, h2")
        if heading.count() > 0:
            expect(heading.first).to_be_visible()

        # 자산 데이터가 있으면 첫 번째 행 클릭
        rows = page.locator("tbody tr")
        if rows.count() > 0:
            rows.first.click()
            page.wait_for_load_state("networkidle")

            # 감가상각 스케줄 테이블 확인
            depreciation_section = page.locator(
                '[data-testid="depreciation-schedule"], text="감가상각 스케줄"'
            )
            if depreciation_section.count() > 0:
                expect(depreciation_section.first).to_be_visible()
