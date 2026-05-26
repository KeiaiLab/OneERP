from __future__ import annotations

from pathlib import Path

from scripts.audit.gates.g2_quality import gate_G2_2_load
from scripts.ci.record_g2_load_evidence import load_status


def test_load_status_uses_perf_baseline_and_scenario() -> None:
    status = load_status("gateway")

    assert status["load_baseline_found"] == 1
    assert status["scenario_defined"] == 1
    assert status["thresholds_passed"] == 1
    assert status["target_rps"] >= 100
    assert status["p95_or_lcp_ms"] <= 2500


def test_g2_2_gate_requires_t3_load_verification_fields() -> None:
    result = gate_G2_2_load("G2-2", "gateway")

    assert result.status == "pass"


def test_all_modules_have_load_scenarios() -> None:
    baselines = sorted(Path("docs/engineering/data").glob("perf-*-baseline.md"))
    scenarios = sorted(Path("tests/load").glob("*/scenarios.js"))

    assert len(baselines) == 47
    assert len(scenarios) == 47
