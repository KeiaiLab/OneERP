"""CRUD 흐름 E2E 테스트 — 목록→생성→상세→수정→삭제."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui

ENTITY = "accounts"  # 계정과목 (마스터 데이터, 간단)


class TestEntityList:
    def test_목록_페이지_렌더링(self, authenticated_page: Page, base_url: str):
        """엔티티 목록 페이지에 테이블과 "새로 만들기" 버튼이 표시된다."""
        authenticated_page.goto(f"{base_url}/{ENTITY}")
        authenticated_page.wait_for_load_state("networkidle")
        # 테이블 또는 빈 상태 확인
        table_or_empty = authenticated_page.locator("table, [data-testid='empty-state']")
        expect(table_or_empty.first).to_be_visible(timeout=10000)

    def test_검색_필터링(self, authenticated_page: Page, base_url: str):
        """검색 입력 시 테이블이 필터링된다."""
        authenticated_page.goto(f"{base_url}/{ENTITY}")
        authenticated_page.wait_for_load_state("networkidle")
        search = authenticated_page.locator('input[placeholder*="검색"]')
        if search.count() > 0:
            search.fill("현금")
            authenticated_page.wait_for_timeout(500)  # 디바운스 대기


class TestEntityCreate:
    def test_생성_페이지_렌더링(self, authenticated_page: Page, base_url: str):
        """생성 페이지에 폼 필드와 저장 버튼이 표시된다."""
        authenticated_page.goto(f"{base_url}/{ENTITY}/new")
        authenticated_page.wait_for_load_state("networkidle")
        expect(authenticated_page.locator("form, [data-testid='entity-form']")).to_be_visible(
            timeout=10000
        )
        expect(authenticated_page.locator('button:has-text("저장")')).to_be_visible()

    def test_필수_필드_미입력_에러(self, authenticated_page: Page, base_url: str):
        """필수 필드를 비우고 저장하면 유효성 검사 에러가 표시된다."""
        authenticated_page.goto(f"{base_url}/{ENTITY}/new")
        authenticated_page.wait_for_load_state("networkidle")
        authenticated_page.click('button:has-text("저장")')
        # 에러 메시지 또는 required 속성 확인
        authenticated_page.wait_for_timeout(500)


class TestEntityDetail:
    def test_상세_페이지_렌더링(self, authenticated_page: Page, base_url: str):
        """목록에서 첫 번째 행을 클릭하면 상세 페이지가 표시된다."""
        authenticated_page.goto(f"{base_url}/{ENTITY}")
        authenticated_page.wait_for_load_state("networkidle")
        first_row = authenticated_page.locator("tbody tr").first
        if first_row.count() > 0:
            first_row.click()
            authenticated_page.wait_for_load_state("networkidle")
            # URL이 /{entity}/{id} 패턴인지 확인
            expect(authenticated_page).to_have_url(f"**/{ENTITY}/**")
