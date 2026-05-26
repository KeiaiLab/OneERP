"""evidence 모듈 단위 테스트."""

from __future__ import annotations

from pathlib import Path

from scripts.engine.evidence import (
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    latest_evidence_for,
    load_meta,
    write_meta,
)


def test_compute_evidence_sha_deterministic() -> None:
    """동일 입력은 동일 sha 를 생성한다."""
    sha1 = compute_evidence_sha(command="pytest", exit_code=0, stdout="passed\n", stderr="")
    sha2 = compute_evidence_sha(command="pytest", exit_code=0, stdout="passed\n", stderr="")
    assert sha1 == sha2
    assert len(sha1) == 64


def test_write_and_load_meta(tmp_path: Path) -> None:
    """EvidenceMeta 를 저장·로드하면 동일 값이 복원된다."""
    meta = EvidenceMeta(
        sha256="a" * 64,
        gate="G1-4",
        module="gateway",
        tier="T1",
        command="pytest gateway",
        executor="ce-executor",
        git_sha="abc1234",
        host="darwin",
        user="phil",
        started_at="2026-04-22T07:00:00Z",
        duration_seconds=42,
        exit_code=0,
        stdout_sha256="b" * 64,
        stderr_sha256="c" * 64,
        artifact_paths=["artifacts/T1/G1-4/gateway/log.txt"],
        verification={"coverage_line_rate": 0.84},
    )
    write_meta(meta, base_dir=tmp_path)
    loaded = load_meta(meta.sha256, base_dir=tmp_path)
    assert loaded == meta


def test_append_index_and_latest(tmp_path: Path) -> None:
    """index.jsonl append 후 latest_evidence_for 가 최신을 반환한다."""
    meta_old = EvidenceMeta(
        sha256="a" * 64,
        gate="G1-4",
        module="gateway",
        tier="T1",
        command="x",
        executor="ce-executor",
        git_sha="abc",
        host="h",
        user="u",
        started_at="2026-04-22T07:00:00Z",
        duration_seconds=1,
        exit_code=0,
        stdout_sha256="b" * 64,
        stderr_sha256="c" * 64,
        artifact_paths=[],
        verification={},
    )
    meta_new_dict = {**meta_old.__dict__, "sha256": "d" * 64, "started_at": "2026-04-22T08:00:00Z"}
    meta_new = EvidenceMeta(**meta_new_dict)
    write_meta(meta_old, base_dir=tmp_path)
    write_meta(meta_new, base_dir=tmp_path)
    append_index(meta_old, base_dir=tmp_path)
    append_index(meta_new, base_dir=tmp_path)

    latest = latest_evidence_for("G1-4", "gateway", "T1", base_dir=tmp_path)
    assert latest is not None
    assert latest.sha256 == "d" * 64
