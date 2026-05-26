"""관리 콘솔 접근 스모크."""

from __future__ import annotations

import pytest


@pytest.mark.skipif(
    True,
    reason="CI T2 에서 재실행",
)
def test_admin_dashboard_requires_auth(page, base_url: str) -> None:
    """미인증 시 로그인 redirect."""
    page.goto(f"{base_url}/(admin)")
    assert "/login" in page.url or "/auth" in page.url


@pytest.mark.skipif(
    True,
    reason="CI T2 에서 재실행 · a11y axe 통합",
)
def test_admin_dashboard_a11y(page, base_url: str) -> None:
    """관리 대시보드 a11y 0 violations (axe-playwright)."""
    page.goto(f"{base_url}/(admin)")
    # axe-playwright-python 미설치 시 플레이스홀더 — CI T2 에서 활성화
    # from axe_playwright_python.sync_playwright import Axe
    # axe = Axe()
    # results = axe.run(page)
    # assert results.violations_count == 0
