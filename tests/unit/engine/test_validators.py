"""validators 모듈 단위 테스트 — 문서 기반 검증."""

from __future__ import annotations

from pathlib import Path

from scripts.engine.evidence import EvidenceMeta, append_index, write_meta
from scripts.engine.validators import (
    GateStatus,
    ValidationSpec,
    validate_evidence,
)


def _write_doc(path: Path, *, lines: int, frontmatter: dict[str, str], sections: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fm = "---\n"
    for k, v in frontmatter.items():
        fm += f"{k}: {v}\n"
    fm += "---\n\n"
    body = "\n".join([f"## {s}\n\n본문 라인 {s}\n" for s in sections])
    filler = "\n".join([f"내용 라인 {i}" for i in range(lines)])
    path.write_text(fm + body + "\n" + filler + "\n")


def test_validate_evidence_short_doc_fails(tmp_path: Path) -> None:
    """최소 라인 수 미달 시 FAIL."""
    doc = tmp_path / "runbook.md"
    _write_doc(doc, lines=10, frontmatter={"owner": "x", "module": "gateway"}, sections=["개요"])
    spec = ValidationSpec(min_lines=150)
    result = validate_evidence(spec, gate="G4-2", module="gateway", doc_path=doc)
    assert result.status == GateStatus.FAIL
    assert "min_lines" in result.reason


def test_validate_evidence_missing_section_fails(tmp_path: Path) -> None:
    """필수 H2 섹션 미포함 시 FAIL."""
    doc = tmp_path / "runbook.md"
    _write_doc(doc, lines=300, frontmatter={"owner": "x"}, sections=["개요"])
    spec = ValidationSpec(
        min_lines=150,
        required_sections=[
            "개요",
            "전제 조건",
            "진단 절차",
            "복구 절차",
            "롤백 절차",
            "에스컬레이션",
        ],
    )
    result = validate_evidence(spec, gate="G4-2", module="gateway", doc_path=doc)
    assert result.status == GateStatus.FAIL
    assert "section" in result.reason.lower()


def test_validate_evidence_missing_frontmatter_fails(tmp_path: Path) -> None:
    """필수 frontmatter 미포함 시 FAIL."""
    doc = tmp_path / "runbook.md"
    _write_doc(
        doc,
        lines=300,
        frontmatter={"owner": "x"},
        sections=["개요", "전제 조건", "진단 절차", "복구 절차", "롤백 절차", "에스컬레이션"],
    )
    spec = ValidationSpec(
        min_lines=150,
        required_sections=[
            "개요",
            "전제 조건",
            "진단 절차",
            "복구 절차",
            "롤백 절차",
            "에스컬레이션",
        ],
        required_frontmatter=["owner", "module", "last_reviewed"],
    )
    result = validate_evidence(spec, gate="G4-2", module="gateway", doc_path=doc)
    assert result.status == GateStatus.FAIL
    assert "frontmatter" in result.reason.lower()


def test_validate_evidence_all_pass(tmp_path: Path) -> None:
    """모든 기준 충족 시 PASS."""
    doc = tmp_path / "runbook.md"
    _write_doc(
        doc,
        lines=300,
        frontmatter={"owner": "phil", "module": "gateway", "last_reviewed": "2026-04-22"},
        sections=["개요", "전제 조건", "진단 절차", "복구 절차", "롤백 절차", "에스컬레이션"],
    )
    spec = ValidationSpec(
        min_lines=150,
        required_sections=[
            "개요",
            "전제 조건",
            "진단 절차",
            "복구 절차",
            "롤백 절차",
            "에스컬레이션",
        ],
        required_frontmatter=["owner", "module", "last_reviewed"],
    )
    result = validate_evidence(spec, gate="G4-2", module="gateway", doc_path=doc)
    assert result.status == GateStatus.PASS


def _seed_evidence(
    tmp_path: Path,
    *,
    gate: str,
    module: str,
    tier: str,
    sha: str,
    ts: str,
    exit_code: int = 0,
    verification: dict[str, object] | None = None,
) -> None:
    meta = EvidenceMeta(
        sha256=sha,
        gate=gate,
        module=module,
        tier=tier,
        command="test",
        executor="ce-executor",
        git_sha="abc",
        host="h",
        user="u",
        started_at=ts,
        duration_seconds=1,
        exit_code=exit_code,
        stdout_sha256="b" * 64,
        stderr_sha256="c" * 64,
        artifact_paths=[],
        verification=verification or {},
    )
    write_meta(meta, base_dir=tmp_path)
    append_index(meta, base_dir=tmp_path)


def test_validate_evidence_tier_missing_not_implemented(tmp_path: Path, monkeypatch) -> None:
    """required_tiers 의 증거가 없으면 NOT_IMPLEMENTED."""
    monkeypatch.chdir(tmp_path)
    spec = ValidationSpec(required_tiers=["T1"])
    result = validate_evidence(spec, gate="G1-4", module="gateway")
    assert result.status == GateStatus.NOT_IMPLEMENTED
    assert result.tiers_met == {"T1": False}


def test_validate_evidence_tier_met_pass(tmp_path: Path, monkeypatch) -> None:
    """required_tiers 증거 있고 verification 충족 시 PASS."""
    monkeypatch.chdir(tmp_path)
    _seed_evidence(
        tmp_path,
        gate="G1-4",
        module="gateway",
        tier="T1",
        sha="a" * 64,
        ts="2026-04-22T07:00:00Z",
        verification={"coverage_line_rate": 0.84, "mutation_score": 0.52},
    )
    spec = ValidationSpec(
        required_tiers=["T1"],
        verification_fields={
            "coverage_line_rate": {"gte": 0.80},
            "mutation_score": {"gte": 0.50},
        },
    )
    result = validate_evidence(spec, gate="G1-4", module="gateway")
    assert result.status == GateStatus.PASS
    assert result.tiers_met == {"T1": True}


def test_validate_evidence_verification_below_threshold_fails(tmp_path: Path, monkeypatch) -> None:
    """verification_fields 임계 미달 시 FAIL."""
    monkeypatch.chdir(tmp_path)
    _seed_evidence(
        tmp_path,
        gate="G1-4",
        module="gateway",
        tier="T1",
        sha="a" * 64,
        ts="2026-04-22T07:00:00Z",
        verification={"coverage_line_rate": 0.70},
    )
    spec = ValidationSpec(
        required_tiers=["T1"],
        verification_fields={"coverage_line_rate": {"gte": 0.80}},
    )
    result = validate_evidence(spec, gate="G1-4", module="gateway")
    assert result.status == GateStatus.FAIL


def test_validate_evidence_verification_above_lte_threshold_fails(
    tmp_path: Path, monkeypatch
) -> None:
    """verification_fields 상한 초과 시 FAIL."""
    monkeypatch.chdir(tmp_path)
    _seed_evidence(
        tmp_path,
        gate="G2-1",
        module="gateway",
        tier="T2",
        sha="d" * 64,
        ts="2026-04-22T07:00:00Z",
        verification={"error_rate_max": 0.002},
    )
    spec = ValidationSpec(
        required_tiers=["T2"],
        verification_fields={"error_rate_max": {"lte": 0.001}},
    )
    result = validate_evidence(spec, gate="G2-1", module="gateway")
    assert result.status == GateStatus.FAIL
