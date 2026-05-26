from __future__ import annotations

from pathlib import Path

from scripts.audit.gates.g2_quality import gate_G2_4_chaos
from scripts.ci.record_g2_chaos_evidence import chaos_status


def test_chaos_status_uses_real_report_and_scenario() -> None:
    status = chaos_status("payroll")

    assert status["chaos_report_found"] == 1
    assert status["scenario_defined"] == 1
    assert status["mttr_minutes"] <= 60
    assert status["report"].endswith("docs/kb/incident/chaos-payroll-2026-04-22.md")
    assert status["scenario"].endswith("tests/chaos/payroll/scenarios.yaml")


def test_g2_4_gate_requires_t3_evidence_with_chaos_verification_fields() -> None:
    result = gate_G2_4_chaos("G2-4", "payroll")

    assert result.status == "pass"


def test_all_modules_have_chaos_scenarios() -> None:
    reports = sorted(Path("docs/kb/incident").glob("chaos-*-2026-04-22.md"))
    scenarios = sorted(Path("tests/chaos").glob("*/scenarios.yaml"))

    assert len(reports) == 47
    assert len(scenarios) == 47
