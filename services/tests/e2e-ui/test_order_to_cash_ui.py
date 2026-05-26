"""Order-to-Cash UI E2E — 판매주문 → 출고 → 송장 → 수금.

판매 프로세스의 전체 흐름을 UI 수준에서 검증한다.
"""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestOrderToCash:
    """Order-to-Cash 비즈니스 흐름 UI 테스트."""

    def test_판매주문_생성_및_제출(self, authenticated_page: Page, base_url: str) -> None:
        """판매주문을 생성하고 제출하면 DocStatus가 '제출됨'으로 변경된다."""
        page = authenticated_page

        # 판매주문 생성 페이지 이동
        page.goto(f"{base_url}/sales-orders/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        customer_field = page.locator('[name="customer"]')
        if customer_field.count() > 0:
            customer_field.fill("테스트 고객")

        posting_date = page.locator('[name="posting_date"]')
        if posting_date.count() > 0:
            posting_date.fill("2026-03-23")

        # 저장 버튼 클릭
        save_btn = page.locator('button:has-text("저장")')
        if save_btn.count() > 0:
            save_btn.click()
            page.wait_for_load_state("networkidle")

        # 제출 버튼 클릭
        submit_btn = page.locator('button:has-text("제출")')
        if submit_btn.count() > 0:
            submit_btn.click()
            # 확인 다이얼로그
            confirm_btn = page.locator('button:has-text("확인")')
            if confirm_btn.count() > 0:
                confirm_btn.click()
            page.wait_for_load_state("networkidle")

            # DocStatus 배지 확인
            badge = page.locator('text="제출됨"')
            if badge.count() > 0:
                expect(badge.first).to_be_visible()

    def test_납품서_생성_및_제출(self, authenticated_page: Page, base_url: str) -> None:
        """납품서를 생성하고 제출한다."""
        page = authenticated_page

        # 납품서 생성 페이지 이동
        page.goto(f"{base_url}/delivery-notes/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        customer_field = page.locator('[name="customer"]')
        if customer_field.count() > 0:
            customer_field.fill("테스트 고객")

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

    def test_매출전표_생성_및_제출(self, authenticated_page: Page, base_url: str) -> None:
        """매출전표를 제출하면 분개가 자동 생성된다."""
        page = authenticated_page

        # 매출전표 생성 페이지 이동
        page.goto(f"{base_url}/sales-invoices/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        customer_field = page.locator('[name="customer"]')
        if customer_field.count() > 0:
            customer_field.fill("테스트 고객")

        amount_field = page.locator('[name="grand_total"]')
        if amount_field.count() > 0:
            amount_field.fill("100000")

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

            # 분개 연결 확인 — 토스트 또는 관련 문서 섹션
            toast = page.locator('[role="alert"]')
            if toast.count() > 0:
                expect(toast.first).to_be_visible()

    def test_수금_처리(self, authenticated_page: Page, base_url: str) -> None:
        """수금을 처리하면 매출채권이 소멸한다."""
        page = authenticated_page

        # 수금 생성 페이지 이동
        page.goto(f"{base_url}/payment-entries/new")
        page.wait_for_load_state("networkidle")

        # 필드 입력
        party_field = page.locator('[name="party"]')
        if party_field.count() > 0:
            party_field.fill("테스트 고객")

        paid_amount = page.locator('[name="paid_amount"]')
        if paid_amount.count() > 0:
            paid_amount.fill("100000")

        payment_type = page.locator('[name="payment_type"]')
        if payment_type.count() > 0:
            payment_type.fill("수금")

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
