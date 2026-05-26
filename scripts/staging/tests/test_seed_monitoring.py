"""seed_monitoring 유닛 테스트 — 30일 SLO 시계열 계약 검증."""

from __future__ import annotations

from scripts.staging.seed_monitoring import build_slo_series


def test_build_slo_series_default_30_days() -> None:
    series = build_slo_series()
    assert len(series) == 30
    first = series[0]
    assert first["day"] == 1
    assert "p95_ms" in first
    assert "error_rate" in first
    assert 0.99 <= first["availability"] <= 1.0
    assert min(row["availability"] for row in series) >= 0.999
    assert max(row["error_rate"] for row in series) <= 0.001
    assert max(row["p95_ms"] for row in series) <= 200
