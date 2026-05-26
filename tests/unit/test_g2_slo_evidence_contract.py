from __future__ import annotations

from scripts.ci.record_g2_slo_evidence import build_slo_payload


def test_build_slo_payload_satisfies_g2_1_thresholds() -> None:
    payload = build_slo_payload("selling")
    observed = payload["observed"]
    assert isinstance(observed, dict)

    assert payload["window_days"] == 30
    assert observed["availability_min"] >= 0.999
    assert observed["error_rate_max"] <= 0.001
    assert observed["p95_ms_max"] <= 200
