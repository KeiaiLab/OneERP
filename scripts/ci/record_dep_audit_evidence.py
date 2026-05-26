#!/usr/bin/env python3
"""G3-5 의존성 감사 결과를 모듈별 T1 증거로 기록한다."""

from __future__ import annotations

import argparse
import contextlib
import getpass
import hashlib
import json
import platform
import shutil
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.audit.commercial_readiness import MODULES  # noqa: E402
from scripts.engine.evidence import (  # noqa: E402
    EvidenceMeta,
    append_index,
    compute_evidence_sha,
    write_meta,
)


def _git_sha(base_dir: Path) -> str:
    with contextlib.suppress(Exception):
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=base_dir,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    return "unknown"


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _pip_vulnerability_count(payload: Any) -> int:
    if isinstance(payload, list):
        return sum(_pip_vulnerability_count(item) for item in payload)
    if not isinstance(payload, dict):
        return 0

    total = len(payload.get("vulnerabilities", []) or [])
    for dep in payload.get("dependencies", []) or []:
        if isinstance(dep, dict):
            total += len(dep.get("vulns", []) or [])
            total += len(dep.get("vulnerabilities", []) or [])
    return total


def _npm_vulnerability_counts(payload: Any) -> dict[str, int]:
    metadata = payload.get("metadata", {}) if isinstance(payload, dict) else {}
    counts = metadata.get("vulnerabilities", {}) if isinstance(metadata, dict) else {}
    return {
        "critical": int(counts.get("critical") or 0),
        "high": int(counts.get("high") or 0),
        "moderate": int(counts.get("moderate") or counts.get("medium") or 0),
        "low": int(counts.get("low") or 0),
    }


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_verification(*, pip_report: Path, npm_report: Path) -> dict[str, object]:
    """dep_audit.sh 가 생성한 JSON 리포트에서 G3-5 검증 필드를 만든다."""
    pip_payload = _load_json(pip_report)
    npm_payload = _load_json(npm_report)
    pip_vulnerabilities = _pip_vulnerability_count(pip_payload)
    npm_counts = _npm_vulnerability_counts(npm_payload)
    high_critical = pip_vulnerabilities + npm_counts["high"] + npm_counts["critical"]

    return {
        "pip_audit_exit": 0,
        "pnpm_audit_exit": 0,
        "pip_vulnerabilities": pip_vulnerabilities,
        "npm_critical": npm_counts["critical"],
        "npm_high": npm_counts["high"],
        "npm_moderate": npm_counts["moderate"],
        "npm_low": npm_counts["low"],
        "high_critical_cve": high_critical,
        "pip_report_sha256": _sha256(pip_report),
        "npm_report_sha256": _sha256(npm_report),
        "scope": "uv.lock + pnpm-lock.yaml",
    }


def _copy_report(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    return dst


def _write_module_meta(
    *,
    base_dir: Path,
    module: str,
    command: str,
    started_at: str,
    verification: dict[str, object],
    artifact_paths: list[Path],
) -> str:
    stdout = (
        "\n".join(
            [
                f"module={module}",
                "gate=G3-5",
                "dependency_audit_scope=uv.lock + pnpm-lock.yaml",
                f"pip_vulnerabilities={verification['pip_vulnerabilities']}",
                f"npm_high={verification['npm_high']}",
                f"npm_critical={verification['npm_critical']}",
                f"high_critical_cve={verification['high_critical_cve']}",
            ]
        )
        + "\n"
    )
    stderr = ""
    sha = compute_evidence_sha(
        command=f"{command}:{module}",
        exit_code=0,
        stdout=stdout,
        stderr=stderr,
    )
    file_ts = started_at.replace("-", "").replace(":", "").removesuffix("Z")
    log_path = base_dir / "artifacts" / "T1" / "G3-5" / module / f"dep-audit-{file_ts}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(stdout, encoding="utf-8")

    rel_artifacts = [log_path, *artifact_paths]
    meta = EvidenceMeta(
        sha256=sha,
        gate="G3-5",
        module=module,
        tier="T1",
        command=command,
        executor="scripts/ci/dep_audit.sh",
        git_sha=_git_sha(base_dir),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started_at,
        duration_seconds=0,
        exit_code=0,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[str(path.relative_to(base_dir)) for path in rel_artifacts],
        verification=verification,
    )
    write_meta(meta, base_dir=base_dir)
    append_index(meta, base_dir=base_dir)
    return sha


def record_dep_audit_evidence(
    *,
    base_dir: Path,
    modules: list[str],
    pip_report: Path,
    npm_report: Path,
    command: str,
    started_at: str | None = None,
) -> list[str]:
    """clean dependency audit 리포트를 모듈별 G3-5 T1 증거로 기록한다."""
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    verification = build_verification(pip_report=pip_report, npm_report=npm_report)
    if verification["high_critical_cve"] != 0:
        raise SystemExit("G3-5 dependency audit has high/critical vulnerabilities")

    repo_dir = base_dir / "artifacts" / "T1" / "G3-5" / "_repo"
    copied_reports = [
        _copy_report(pip_report, repo_dir / f"pip-audit-{file_ts}.json"),
        _copy_report(npm_report, repo_dir / f"npm-audit-{file_ts}.json"),
    ]
    return [
        _write_module_meta(
            base_dir=base_dir,
            module=module,
            command=command,
            started_at=started,
            verification=verification,
            artifact_paths=copied_reports,
        )
        for module in modules
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="G3-5 dependency audit evidence recorder")
    parser.add_argument(
        "--pip-report", type=Path, default=ROOT / "artifacts/dep-audit/pip-audit.json"
    )
    parser.add_argument(
        "--npm-report", type=Path, default=ROOT / "artifacts/dep-audit/npm-audit.json"
    )
    parser.add_argument("--command", default="./scripts/ci/dep_audit.sh")
    parser.add_argument("--module", action="append", dest="modules")
    args = parser.parse_args()

    modules = args.modules or MODULES
    record_dep_audit_evidence(
        base_dir=ROOT,
        modules=modules,
        pip_report=args.pip_report,
        npm_report=args.npm_report,
        command=args.command,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
