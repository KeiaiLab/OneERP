"""accounting · 회계기간 개설 / 마감 플로우."""

from __future__ import annotations

import os

import pytest

_FE_URL = os.environ.get("ONEERP_FE_URL")


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_period_open_flow(page, fe_url: str) -> None:
    """신규 회계기간 개설 시 상태가 OPEN 으로 표시된다."""
    page.goto(f"{fe_url}/accounting/periods")
    page.get_by_test_id("period-new-button").click()
    page.get_by_test_id("period-name-input").fill("2026-Q2")
    page.get_by_test_id("period-save-button").click()
    assert page.get_by_test_id("period-status-OPEN").is_visible()


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_period_close_flow(page, fe_url: str) -> None:
    """OPEN 상태 기간을 마감하면 CLOSED 로 전환된다."""
    page.goto(f"{fe_url}/accounting/periods")
    page.get_by_test_id("period-close-button").first.click()
    page.get_by_test_id("period-confirm-close").click()
    assert page.get_by_test_id("period-status-CLOSED").is_visible()
