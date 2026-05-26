from __future__ import annotations

from scripts.ci.record_g2_perf_regression_evidence import perf_status


def test_perf_status_uses_existing_baseline_doc() -> None:
    status = perf_status("selling")

    assert status["baseline_found"] == 1
    assert status["regressions_found"] == 0
    assert status["baseline_lines"] >= 20
