"""G1-3 운영 통합 계약 — payroll."""

from __future__ import annotations

from pathlib import Path

MODULE = "payroll"
ROOT = Path(__file__).resolve().parents[3]


def test_operator_docs_link_module_runtime_surfaces() -> None:
    runbook = ROOT / "docs" / "ops" / f"runbook-{MODULE}.md"
    manual = ROOT / "docs" / "user-manual" / f"{MODULE}.md"
    tutorial = ROOT / "docs" / "tutorials" / f"{MODULE}.md"

    assert runbook.exists()
    assert manual.exists()
    assert tutorial.exists()
    assert "python3 scripts/audit/commercial_readiness.py" in runbook.read_text(encoding="utf-8")
