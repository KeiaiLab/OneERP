"""G1-4 단위 테스트 계약 — payroll."""

from __future__ import annotations

import json
from pathlib import Path

MODULE = "payroll"
ROOT = Path(__file__).resolve().parents[3]
SERVICE_DIR = ROOT / "services/finance/payroll"


def test_service_unit_suite_exists() -> None:
    tests = sorted((SERVICE_DIR / "tests").rglob("test_*.py"))

    assert len(tests) >= 2


def test_unit_contract_has_integration_surface() -> None:
    integration = sorted((ROOT / "tests" / "integration" / MODULE).glob("test_*.py"))

    assert len(integration) >= 3


def test_unit_contract_links_runbook_and_uat() -> None:
    assert (ROOT / "docs" / "ops" / f"runbook-{MODULE}.md").exists()
    assert (ROOT / "docs" / "governance" / "commercial" / f"{MODULE}.md").exists()


def test_coverage_contract_meets_threshold() -> None:
    payload = json.loads((ROOT / "artifacts" / "T1" / "G1-4" / MODULE / "coverage.json").read_text())

    assert payload["totals"]["percent_covered"] >= 80.0


def test_mutation_contract_meets_threshold() -> None:
    payload = json.loads(
        (ROOT / "artifacts" / "T1" / "G1-4" / MODULE / "mutmut-summary.json").read_text()
    )

    assert payload["total"] >= 5
    assert payload["score_pct"] >= 50.0
