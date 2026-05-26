from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_total_commercial_gate_script가_핵심_단계를_포함한다() -> None:
    path = ROOT / "scripts/ci/run_total_commercial_gate.sh"
    assert path.exists(), f"스크립트 없음: {path}"
    text = path.read_text(encoding="utf-8")
    catalog_check_idx = text.index("check_saas_release_catalog.py")
    strict_check_idx = text.index("commercial_readiness.py --verify --strict")
    release_gate_idx = text.index("./scripts/ci/run_release_gate.sh")
    evidence_check_idx = text.index("check_release_rehearsal_evidence.py")
    assert catalog_check_idx < release_gate_idx
    assert catalog_check_idx < strict_check_idx
    assert release_gate_idx < evidence_check_idx
    assert evidence_check_idx < strict_check_idx

    for snippet in (
        "SaaS release catalog 불변성 확인",
        "check_saas_release_catalog.py",
        "성능/복구/운영 필수 근거 파일 확인",
        "check_release_rehearsal_evidence.py",
        "47모듈 x 23게이트 strict 상용 준비도 확인",
        "commercial_readiness.py --verify --strict --format text",
    ):
        assert snippet in text


def test_evidence_checker는_presence_check_문구와_필수파일을_갖는다() -> None:
    path = ROOT / "scripts/ci/check_release_rehearsal_evidence.py"
    assert path.exists(), f"스크립트 없음: {path}"
    text = path.read_text(encoding="utf-8")

    for snippet in (
        "missing required rehearsal evidence files:",
        "release rehearsal evidence presence check ok",
        "docs/infra/ops/backup-restore.md",
        "docs/ops/runbook-db-backup-restore.md",
        "docs/generated/commercial-status.md",
    ):
        assert snippet in text


def test_makefile이_total_commercial_gate_타깃을_노출한다() -> None:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "total-commercial-gate:" in text
