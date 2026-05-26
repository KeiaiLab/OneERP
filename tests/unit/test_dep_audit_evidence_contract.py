from __future__ import annotations

import json
from pathlib import Path

from scripts.audit.gates.g3_security import gate_G3_5_dep
from scripts.ci.record_dep_audit_evidence import (
    build_verification,
    record_dep_audit_evidence,
)
from scripts.engine.validators import GateStatus


def _write_reports(tmp_path: Path) -> tuple[Path, Path]:
    pip_report = tmp_path / "pip-audit.json"
    npm_report = tmp_path / "npm-audit.json"
    pip_report.write_text(
        json.dumps({"dependencies": [{"name": "fastapi", "version": "0", "vulns": []}]}),
        encoding="utf-8",
    )
    npm_report.write_text(
        json.dumps(
            {
                "metadata": {
                    "vulnerabilities": {
                        "critical": 0,
                        "high": 0,
                        "moderate": 1,
                        "low": 2,
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return pip_report, npm_report


def test_build_verification_counts_clean_reports(tmp_path: Path) -> None:
    pip_report, npm_report = _write_reports(tmp_path)

    verification = build_verification(pip_report=pip_report, npm_report=npm_report)

    assert verification["pip_audit_exit"] == 0
    assert verification["pnpm_audit_exit"] == 0
    assert verification["high_critical_cve"] == 0
    assert verification["npm_high"] == 0
    assert verification["npm_critical"] == 0


def test_record_dep_audit_evidence_makes_g3_5_gate_pass(
    tmp_path: Path,
    monkeypatch,
) -> None:
    pip_report, npm_report = _write_reports(tmp_path)

    record_dep_audit_evidence(
        base_dir=tmp_path,
        modules=["selling"],
        pip_report=pip_report,
        npm_report=npm_report,
        command="./scripts/ci/dep_audit.sh",
        started_at="2026-05-07T00:00:00Z",
    )

    monkeypatch.chdir(tmp_path)
    result = gate_G3_5_dep("G3-5", "selling")

    assert result.status == GateStatus.PASS
    assert result.tiers_met == {"T1": True}
