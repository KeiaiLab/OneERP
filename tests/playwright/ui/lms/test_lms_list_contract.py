"""G1-5 Playwright UI 계약 — lms 목록 화면."""

from __future__ import annotations

from pathlib import Path

import pytest

MODULE = "lms"
ROOT = Path(__file__).resolve().parents[4]

pytestmark = pytest.mark.playwright


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_lms_list_scenario_documented() -> None:
    manual = _read(f"docs/user-manual/{MODULE}.md")
    tutorial = _read(f"docs/tutorials/{MODULE}.md")
    uat = _read(f"docs/governance/commercial/{MODULE}.md")

    assert MODULE in manual
    assert MODULE in tutorial
    assert MODULE in uat
    assert "목록" in manual or "주요 화면" in manual
    assert "test_cleanup_20260507" in uat
