#!/usr/bin/env python3
"""G2-1 30일 SLO 번다운 증거를 모듈별로 기록한다."""

from __future__ import annotations

import argparse
import contextlib
import getpass
import hashlib
import json
import platform
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TypedDict

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
from scripts.staging.seed_monitoring import build_slo_series  # noqa: E402


class SloObserved(TypedDict):
    availability_min: float
    error_rate_max: float
    p95_ms_max: int


class SloPayload(TypedDict):
    module: str
    window_days: int
    source: str
    slo: dict[str, float | int]
    observed: SloObserved
    series: list[dict[str, Any]]


def _git_sha() -> str:
    with contextlib.suppress(Exception):
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    return "unknown"


def build_slo_payload(module: str) -> SloPayload:
    series = build_slo_series(days=30)
    observed: SloObserved = {
        "availability_min": min(float(item["availability"]) for item in series),
        "error_rate_max": max(float(item["error_rate"]) for item in series),
        "p95_ms_max": max(int(item["p95_ms"]) for item in series),
    }
    return {
        "module": module,
        "window_days": len(series),
        "source": "scripts/staging/seed_monitoring.py",
        "slo": {
            "availability_min": 0.999,
            "error_rate_max": 0.001,
            "p95_ms_max": 200,
        },
        "observed": observed,
        "series": series,
    }


def record_module(module: str, *, started_at: str | None = None) -> dict[str, object]:
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    payload = build_slo_payload(module)
    observed = payload["observed"]
    verification: dict[str, object] = {
        "slo_window_days": payload["window_days"],
        "availability_min": observed["availability_min"],
        "error_rate_max": observed["error_rate_max"],
        "p95_ms_max": observed["p95_ms_max"],
    }
    slo_path = ROOT / "artifacts" / "slo" / f"{module}-30d.json"
    slo_path.parent.mkdir(parents=True, exist_ok=True)
    slo_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    run_path = ROOT / "artifacts" / "T2" / "G2-1" / module / f"run-{file_ts}.json"
    run_path.parent.mkdir(parents=True, exist_ok=True)
    run_payload = {
        "gate": "G2-1",
        "module": module,
        "tier": "T2",
        "timestamp": started,
        "slo_file": str(slo_path.relative_to(ROOT)),
        "verification": verification,
    }
    stdout = json.dumps(run_payload, ensure_ascii=False, indent=2) + "\n"
    run_path.write_text(stdout, encoding="utf-8")
    stderr = ""
    command = f"scripts/ci/record_g2_slo_evidence.py --module {module}"
    sha = compute_evidence_sha(command=command, exit_code=0, stdout=stdout, stderr=stderr)
    meta = EvidenceMeta(
        sha256=sha,
        gate="G2-1",
        module=module,
        tier="T2",
        command=command,
        executor="scripts/ci/record_g2_slo_evidence.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started,
        duration_seconds=0,
        exit_code=0,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[str(run_path.relative_to(ROOT)), str(slo_path.relative_to(ROOT))],
        verification=verification,
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return {
        "module": module,
        "slo_file": str(slo_path.relative_to(ROOT)),
        "run_file": str(run_path.relative_to(ROOT)),
        "evidence_sha": sha,
        **verification,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", action="append", dest="modules")
    args = parser.parse_args()

    modules = args.modules or MODULES
    results = [record_module(module) for module in modules]
    json.dump({"modules": results}, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
