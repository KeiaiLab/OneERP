"""accounting · 예산 설정 / 집행률 조회 플로우."""

from __future__ import annotations

import os

import pytest

_FE_URL = os.environ.get("ONEERP_FE_URL")


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_budget_create_flow(page, fe_url: str) -> None:
    """예산 생성 화면에서 계정·금액을 입력 후 저장 시 목록에 반영된다."""
    page.goto(f"{fe_url}/accounting/budgets/new")
    page.get_by_test_id("budget-account-select").click()
    page.get_by_test_id("budget-amount-input").fill("5000000")
    page.get_by_test_id("budget-save-button").click()
    assert page.get_by_test_id("toast-success").is_visible()


@pytest.mark.playwright
@pytest.mark.skipif(not _FE_URL, reason="FE server not running (ONEERP_FE_URL 미설정)")
def test_budget_execution_rate_view(page, fe_url: str) -> None:
    """예산 집행률 대시보드가 렌더된다."""
    page.goto(f"{fe_url}/accounting/budgets")
    assert page.get_by_test_id("budget-execution-chart").is_visible()
