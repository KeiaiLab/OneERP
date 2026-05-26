from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "audit"))

import commercial_readiness  # noqa: E402
import wave_entry_check  # noqa: E402


def test_commercial_readiness_json이_전체_완료_요약을_포함한다() -> None:
    result = subprocess.run(
        ["python3", "scripts/audit/commercial_readiness.py", "--format", "json"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)
    summary = payload["summary"]
    reports = payload["reports"]
    assert summary["total_judgments"] == 1081
    assert summary["total"] == summary["total_judgments"]
    assert "overall_complete" in summary
    assert "commercial_ready_modules" in summary
    assert isinstance(reports, list)
    assert len(reports) == 47
    first_report = reports[0]
    assert set(first_report) >= {"module", "label", "gates"}
    assert isinstance(first_report["gates"], list)
    computed_passed = sum(
        1 for report in reports for gate in report["gates"] if gate["status"] == "pass"
    )
    computed_ready = sum(1 for report in reports if report["label"] == "commercial-ready")
    assert summary["passed"] == computed_passed
    assert summary["commercial_ready_modules"] == computed_ready
    assert summary["overall_complete"] == (
        computed_passed == summary["total_judgments"] and computed_ready == len(reports)
    )


def test_wave_entry_check가_23_23_전수통과를_계산한다() -> None:
    reports = dict.fromkeys(
        wave_entry_check.WAVES[4], commercial_readiness.Label.PRE_COMMERCIAL.value
    )
    reports[wave_entry_check.WAVES[4][0]] = commercial_readiness.Label.COMMERCIAL_READY.value

    status = wave_entry_check.assess_wave(4, reports)

    assert status.pre_commercial_or_better == len(status.modules)
    assert status.commercial_ready == 1
    assert status.exit_complete is False
