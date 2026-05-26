"""ce-executor 가 호출 — Bash 실행 결과를 artifacts/ 에 증거로 기록."""

from __future__ import annotations

import contextlib
import getpass
import hashlib
import platform
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from scripts.engine.evidence import (
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    write_meta,
)


def _git_sha() -> str:
    """현재 HEAD 의 short git sha. 실패 시 unknown."""
    with contextlib.suppress(Exception):
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    return "unknown"


def record_execution(
    *,
    command: str,
    stdout: str,
    stderr: str,
    exit_code: int,
    duration_seconds: int,
    gate: str,
    module: str,
    tier: str,
    verification: dict[str, object] | None = None,
    extra_artifacts: list[Path] | None = None,
    base_dir: Path | None = None,
) -> str:
    """실행 결과 하나를 증거로 기록하고 sha 반환.

    생성물:
      - artifacts/<tier>/<gate>/<module>/<ts>.log (원본 stdout/stderr)
      - artifacts/_meta/<sha>.json (개별 메타)
      - artifacts/_meta/index.jsonl (append-only 인덱스)
    """
    base = base_dir or Path.cwd()
    sha = compute_evidence_sha(command=command, exit_code=exit_code, stdout=stdout, stderr=stderr)
    ts = datetime.now(UTC).strftime("%Y-%m-%dT%H%MZ")

    log_dir = base / f"artifacts/{tier}/{gate}/{module}"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"{ts}.log"
    log_path.write_text(
        f"$ {command}\n[exit={exit_code}]\n--- stdout ---\n{stdout}\n--- stderr ---\n{stderr}\n"
    )

    artifact_paths = [str(log_path.relative_to(base))]
    if extra_artifacts:
        artifact_paths.extend(str(p.relative_to(base)) for p in extra_artifacts)

    meta = EvidenceMeta(
        sha256=sha,
        gate=gate,
        module=module,
        tier=tier,
        command=command,
        executor="ce-executor",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        duration_seconds=duration_seconds,
        exit_code=exit_code,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=artifact_paths,
        verification=verification or {},
    )
    write_meta(meta, base_dir=base)
    append_index(meta, base_dir=base)
    return sha
