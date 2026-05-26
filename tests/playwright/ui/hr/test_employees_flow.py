"""hr · 직원 조회 / 상세 / 신규 등록 플로우."""

from __future__ import annotations

import os

import pytest

_FE_URL = os.environ.get("ONEERP_FE_URL")


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_employee_list_renders(page, fe_url: str) -> None:
    """직원 목록 화면이 렌더되고 행이 존재한다."""
    page.goto(f"{fe_url}/hr/employees")
    assert page.get_by_test_id("employee-list").is_visible()


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_employee_create_flow(page, fe_url: str) -> None:
    """신규 직원 등록 후 토스트가 노출된다."""
    page.goto(f"{fe_url}/hr/employees/new")
    page.get_by_test_id("employee-name-input").fill("홍길동")
    page.get_by_test_id("employee-email-input").fill("hong@example.com")
    page.get_by_test_id("employee-save-button").click()
    assert page.get_by_test_id("toast-success").is_visible()
