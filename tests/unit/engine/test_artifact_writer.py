"""artifact_writer 단위 테스트 — record_execution 의 로그·메타·인덱스 3종 생성 확인."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.engine.artifact_writer import record_execution


def test_record_execution_creates_log_meta_and_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """명령 실행 결과를 artifacts/ 아래 3종(log·meta·index)으로 기록."""
    monkeypatch.chdir(tmp_path)
    sha = record_execution(
        command="echo hello",
        stdout="hello\n",
        stderr="",
        exit_code=0,
        duration_seconds=1,
        gate="G1-4",
        module="gateway",
        tier="T1",
        verification={"coverage_line_rate": 0.82},
    )

    # 1. 개별 메타 JSON 생성
    assert (tmp_path / f"artifacts/_meta/{sha}.json").exists()

    # 2. 인덱스에 append
    index = (tmp_path / "artifacts/_meta/index.jsonl").read_text()
    assert sha in index

    # 3. 로그 파일 생성
    log_files = list((tmp_path / "artifacts/T1/G1-4/gateway").glob("*.log"))
    assert len(log_files) == 1
    assert "hello" in log_files[0].read_text()


def test_record_execution_returns_deterministic_sha(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """동일 명령·exit·stdout·stderr 는 동일 sha 를 반환."""
    monkeypatch.chdir(tmp_path)
    sha1 = record_execution(
        command="pytest",
        stdout="ok\n",
        stderr="",
        exit_code=0,
        duration_seconds=1,
        gate="G1-4",
        module="gateway",
        tier="T1",
    )
    (tmp_path / "artifacts").rename(tmp_path / "artifacts_old")
    sha2 = record_execution(
        command="pytest",
        stdout="ok\n",
        stderr="",
        exit_code=0,
        duration_seconds=1,
        gate="G1-4",
        module="gateway",
        tier="T1",
    )
    assert sha1 == sha2
