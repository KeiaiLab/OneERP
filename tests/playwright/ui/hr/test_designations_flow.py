"""hr · 직위 변경 플로우."""

from __future__ import annotations

import os

import pytest

_FE_URL = os.environ.get("ONEERP_FE_URL")


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_designation_list_renders(page, fe_url: str) -> None:
    """직위 목록이 렌더된다."""
    page.goto(f"{fe_url}/hr/designations")
    assert page.get_by_test_id("designation-list").is_visible()


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_designation_change_flow(page, fe_url: str) -> None:
    """직원 직위 변경 후 이력이 추가된다."""
    page.goto(f"{fe_url}/hr/designations")
    page.get_by_test_id("designation-change-button").first.click()
    page.get_by_test_id("designation-select").click()
    page.get_by_test_id("designation-confirm-button").click()
    assert page.get_by_test_id("toast-success").is_visible()
