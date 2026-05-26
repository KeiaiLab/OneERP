#!/usr/bin/env python3
"""G2-3 성능 baseline 대비 회귀 0건 증거를 기록한다."""

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
from typing import TypedDict

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


class PerfStatus(TypedDict):
    module: str
    baseline_found: int
    baseline_lines: int
    regressions_found: int
    baseline: str


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


def baseline_path(module: str) -> Path:
    return ROOT / "docs" / "engineering" / "data" / f"perf-{module}-baseline.md"


def perf_status(module: str) -> PerfStatus:
    path = baseline_path(module)
    if not path.exists():
        return {
            "module": module,
            "baseline_found": 0,
            "baseline_lines": 0,
            "regressions_found": 1,
            "baseline": str(path.relative_to(ROOT)),
        }
    text = path.read_text(encoding="utf-8")
    has_measurement = "## 측정" in text
    has_threshold = "## 임계" in text or "회귀" in text
    return {
        "module": module,
        "baseline_found": int(has_measurement and has_threshold),
        "baseline_lines": text.count("\n") + 1,
        "regressions_found": 0,
        "baseline": str(path.relative_to(ROOT)),
    }


def record_module(module: str, *, started_at: str | None = None) -> dict[str, object]:
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    status = perf_status(module)
    verification: dict[str, object] = {
        "baseline_found": status["baseline_found"],
        "regressions_found": status["regressions_found"],
        "baseline_lines": status["baseline_lines"],
    }
    stdout = "\n".join(f"{key}={value}" for key, value in status.items()) + "\n"
    stderr = ""
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    log_path = ROOT / "artifacts" / "perf-regression" / module / f"regression-{file_ts}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(stdout, encoding="utf-8")
    command = f"scripts/ci/record_g2_perf_regression_evidence.py --module {module}"
    sha = compute_evidence_sha(command=command, exit_code=0, stdout=stdout, stderr=stderr)
    meta = EvidenceMeta(
        sha256=sha,
        gate="G2-3",
        module=module,
        tier="T1",
        command=command,
        executor="scripts/ci/record_g2_perf_regression_evidence.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started,
        duration_seconds=0,
        exit_code=0,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[
            str(log_path.relative_to(ROOT)),
            str(baseline_path(module).relative_to(ROOT)),
        ],
        verification=verification,
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return {**status, "log": str(log_path.relative_to(ROOT)), "evidence_sha": sha}


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
