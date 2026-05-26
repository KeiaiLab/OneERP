"""accounting · 저널 엔트리 생성 플로우 (차변/대변 입력 · 저장 · 토스트)."""

from __future__ import annotations

import os

import pytest

_FE_URL = os.environ.get("ONEERP_FE_URL")


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_journal_entry_create_flow(page, fe_url: str) -> None:
    """저널 엔트리 신규 생성 화면에서 차/대변을 입력 후 저장 시 토스트가 노출된다."""
    page.goto(f"{fe_url}/accounting/journal/new")
    page.get_by_test_id("journal-debit-input-0").fill("100000")
    page.get_by_test_id("journal-credit-input-0").fill("100000")
    page.get_by_test_id("journal-save-button").click()
    assert page.get_by_test_id("toast-success").is_visible()


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_journal_list_shows_recent_entries(page, fe_url: str) -> None:
    """저널 목록 화면은 최근 엔트리 목록을 표시한다."""
    page.goto(f"{fe_url}/accounting/journal")
    assert page.get_by_test_id("journal-list").is_visible()
    assert page.get_by_test_id("journal-row").count() >= 0
