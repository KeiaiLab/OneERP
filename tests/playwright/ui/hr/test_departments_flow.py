"""hr · 부서 목록 / 재편 플로우."""

from __future__ import annotations

import os

import pytest

_FE_URL = os.environ.get("ONEERP_FE_URL")


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_department_list_renders(page, fe_url: str) -> None:
    """부서 목록이 트리 형태로 렌더된다."""
    page.goto(f"{fe_url}/hr/departments")
    assert page.get_by_test_id("department-tree").is_visible()


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_department_reorganize_flow(page, fe_url: str) -> None:
    """부서 이름 변경(재편) 후 목록에 반영된다."""
    page.goto(f"{fe_url}/hr/departments")
    page.get_by_test_id("department-edit-button").first.click()
    page.get_by_test_id("department-name-input").fill("재무팀(개편)")
    page.get_by_test_id("department-save-button").click()
    assert page.get_by_test_id("toast-success").is_visible()
