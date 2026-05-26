from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RELEASE_CRITERIA = ROOT / ".planning" / "program" / "releases" / "RELEASE-CRITERIA.md"


def test_release_criteria_separates_pilot_and_saas_production_gates() -> None:
    text = RELEASE_CRITERIA.read_text(encoding="utf-8")

    assert "## 파일럿 출시 최소 기준" in text
    assert "## SaaS production 출시 기준" in text
    assert "`./scripts/ci/run.sh`" in text
    assert "`./scripts/ci/run_total_commercial_gate.sh`" in text


def test_release_criteria_requires_strict_commercial_and_immutable_catalog() -> None:
    text = RELEASE_CRITERIA.read_text(encoding="utf-8")

    for snippet in (
        "`python3 scripts/ci/check_saas_release_catalog.py`",
        "`python3 scripts/audit/commercial_readiness.py --verify --strict --format text`",
        "`passed == 1081`",
        "`commercial_ready_modules == 47`",
        "`latest`",
        "`targetRevision: main`",
    ):
        assert snippet in text
