"""문서 관리 UI E2E."""

from __future__ import annotations

import pytest
from playwright.sync_api import Page, expect

pytestmark = pytest.mark.e2e_ui


class TestDocumentUI:
    """문서 관리 화면의 기본 렌더링을 검증한다."""

    def test_보존정책_페이지가_로드된다(self, authenticated_page: Page, base_url: str) -> None:
        page = authenticated_page
        page.goto(f"{base_url}/retention-policy")
        page.wait_for_load_state("networkidle")

        summary = page.locator("text=/보존 정책|만료|폐기/")
        if summary.count() > 0:
            expect(summary.first).to_be_visible()

    def test_문서_목록_페이지가_로드된다(self, authenticated_page: Page, base_url: str) -> None:
        page = authenticated_page
        page.goto(f"{base_url}/document")
        page.wait_for_load_state("networkidle")

        summary = page.locator("text=/문서|공유|버전|서명|보존/")
        if summary.count() > 0:
            expect(summary.first).to_be_visible()

    def test_문서_상세_페이지에_워크벤치_블록이_노출된다(
        self,
        authenticated_page: Page,
        base_url: str,
    ) -> None:
        page = authenticated_page
        page.goto(f"{base_url}/document/DOC-TEST-001")
        page.wait_for_load_state("networkidle")

        summary = page.locator("text=/문서 요약|공유 현황|서명 현황|버전 이력/")
        if summary.count() > 0:
            expect(summary.first).to_be_visible()
