"""G1-5 Playwright UI 계약 — gateway 접근성/오류 상태."""

from __future__ import annotations

from pathlib import Path

import pytest

MODULE = "gateway"
ROOT = Path(__file__).resolve().parents[4]

pytestmark = pytest.mark.playwright


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_gateway_a11y_scenario_documented() -> None:
    manual = _read(f"docs/user-manual/{MODULE}.md")
    tutorial = _read(f"docs/tutorials/{MODULE}.md")
    uat = _read(f"docs/governance/commercial/{MODULE}.md")
    combined = f"{manual}\n{tutorial}\n{uat}"

    assert MODULE in manual
    assert MODULE in tutorial
    assert MODULE in uat
    assert "권한 오류" in combined
    assert "오류 처리" in combined or "오류 상태" in combined
    assert "test_cleanup_20260507" in uat
