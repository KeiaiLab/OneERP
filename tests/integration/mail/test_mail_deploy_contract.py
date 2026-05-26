"""G1-3 배포 통합 계약 — mail."""

from __future__ import annotations

from pathlib import Path

MODULE = "mail"
ROOT = Path(__file__).resolve().parents[3]


def test_release_chart_exposes_service_and_route() -> None:
    chart = ROOT / "deploy" / "charts" / MODULE

    assert (chart / "templates" / "deployment.yaml").exists()
    assert (chart / "templates" / "service.yaml").exists()
    assert (chart / "templates" / "httproute.yaml").exists()
    assert (chart / "values-release.yaml").exists()
