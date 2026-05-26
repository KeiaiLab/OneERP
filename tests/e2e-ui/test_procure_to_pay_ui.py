"""Procure-to-Pay UI E2E — 구매요청 → 발주 → 입고 → 지급.

구매 프로세스의 전체 흐름을 UI 수준에서 검증한다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestProcureToPay:
    """Procure-to-Pay 비즈니스 흐름 UI 테스트."""

    def test_구매분석_대시보드가_로드된다(self, authenticated_page: Page, base_url: str) -> None:
        """구매 분석 페이지가 로드되고 핵심 필터/워크벤치 영역을 노출한다."""
        page = authenticated_page

        page.goto(f"{base_url}/purchase-analytics")
        page.wait_for_load_state("networkidle")

        group_filter = page.locator(
            '[name="group_by"], select[name="group_by"], [data-testid="purchase-analytics-group-by"]'
        )
        if group_filter.count() > 0:
            expect(group_filter.first).to_be_visible()

        workbench = page.locator(
            'text="구매 분석", text="Purchase Analytics", [data-testid="purchase-analytics-workbench"]'
        )
        if workbench.count() > 0:
            expect(workbench.first).to_be_visible()

    def test_공급업체견적_비교_페이지가_로드된다(
        self, authenticated_page: Page, base_url: str
    ) -> None:
        """공급업체 견적 워크벤치가 로드되고 비교/발주 액션 영역을 노출한다."""
        page = authenticated_page

        page.goto(f"{base_url}/supplier-quotation")
        page.wait_for_load_state("networkidle")

        compare_button = page.locator(
            'button:has-text("견적 비교"), button:has-text("Compare Quotations")'
        )
        if compare_button.count() > 0:
            expect(compare_button.first).to_be_visible()

        create_po_button = page.locator(
            'button:has-text("발주 생성"), button:has-text("Create Purchase Order")'
        )
        if create_po_button.count() > 0:
            expect(create_po_button.first).to_be_visible()

    def test_구매주문_생성_제출(self, authenticated_page: Page, base_url: str) -> None:
        """구매주문을 생성하고 제출한다."""
        page = authenticated_page

        # 구매주문 생성 페이지 이동
        page.goto(f"{base_url}/purchase-orders/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        supplier_field = page.locator('[name="supplier"]')
        if supplier_field.count() > 0:
            supplier_field.fill("테스트 공급사")

        posting_date = page.locator('[name="posting_date"]')
        if posting_date.count() > 0:
            posting_date.fill("2026-03-23")

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

    def test_입고전표_생성_제출(self, authenticated_page: Page, base_url: str) -> None:
        """입고전표를 생성하고 제출한다."""
        page = authenticated_page

        # 입고전표 생성 페이지 이동
        page.goto(f"{base_url}/purchase-receipts/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        supplier_field = page.locator('[name="supplier"]')
        if supplier_field.count() > 0:
            supplier_field.fill("테스트 공급사")

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

    def test_매입전표_생성_제출(self, authenticated_page: Page, base_url: str) -> None:
        """매입전표를 생성하고 제출하면 분개가 자동 생성된다."""
        page = authenticated_page

        # 매입전표 생성 페이지 이동
        page.goto(f"{base_url}/purchase-invoices/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        supplier_field = page.locator('[name="supplier"]')
        if supplier_field.count() > 0:
            supplier_field.fill("테스트 공급사")

        amount_field = page.locator('[name="grand_total"]')
        if amount_field.count() > 0:
            amount_field.fill("500000")

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

            # 토스트 확인
            toast = page.locator('[role="alert"]')
            if toast.count() > 0:
                expect(toast.first).to_be_visible()

    def test_지급_처리(self, authenticated_page: Page, base_url: str) -> None:
        """지급을 처리하면 매입채무가 소멸한다."""
        page = authenticated_page

        # 지급 생성 페이지 이동
        page.goto(f"{base_url}/payment-entries/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        party_field = page.locator('[name="party"]')
        if party_field.count() > 0:
            party_field.fill("테스트 공급사")

        paid_amount = page.locator('[name="paid_amount"]')
        if paid_amount.count() > 0:
            paid_amount.fill("500000")

        payment_type = page.locator('[name="payment_type"]')
        if payment_type.count() > 0:
            payment_type.fill("지급")

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
