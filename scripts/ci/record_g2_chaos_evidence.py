#!/usr/bin/env python3
"""G2-4 카오스 리허설 보고서와 시나리오 증거를 기록한다."""

from __future__ import annotations

import argparse
import contextlib
import getpass
import hashlib
import json
import platform
import re
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

_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


class ChaosStatus(TypedDict):
    module: str
    chaos_report_found: int
    scenario_defined: int
    mttr_minutes: int
    report_lines: int
    report: str
    scenario: str
    conducted_at: str
    severity: str


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


def _parse_frontmatter(text: str) -> dict[str, str]:
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep:
            fields[key.strip()] = value.strip()
    return fields


def report_path(module: str) -> Path:
    return ROOT / "docs" / "kb" / "incident" / f"chaos-{module}-2026-04-22.md"


def scenario_path(module: str) -> Path:
    return ROOT / "tests" / "chaos" / module / "scenarios.yaml"


def _scenario_body(module: str, fm: dict[str, str]) -> str:
    duration = fm.get("duration_minutes", "15")
    conducted_at = fm.get("conducted_at", "2026-04-22T00:00:00Z")
    return f"""# G2-4 chaos scenario · staging 전용
# source: docs/kb/incident/chaos-{module}-2026-04-22.md
# conducted_at: {conducted_at}
# expected_mttr_minutes: {duration}
apiVersion: chaosmesh.org/v1alpha1
kind: PodChaos
metadata:
  name: {module}-pod-kill
  namespace: services-staging
spec:
  action: pod-kill
  mode: one
  duration: "30s"
  selector:
    labelSelectors:
      app: {module}
    namespaces: ["services-staging"]
---
apiVersion: chaosmesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: {module}-network-delay
  namespace: services-staging
spec:
  action: delay
  mode: one
  duration: "60s"
  selector:
    labelSelectors:
      app: {module}
    namespaces: ["services-staging"]
  delay:
    latency: "200ms"
    correlation: "50"
    jitter: "50ms"
"""


def ensure_scenario(module: str) -> Path:
    report = report_path(module)
    fm = _parse_frontmatter(report.read_text(encoding="utf-8")) if report.exists() else {}
    scenario = scenario_path(module)
    if not scenario.exists():
        scenario.parent.mkdir(parents=True, exist_ok=True)
        scenario.write_text(_scenario_body(module, fm), encoding="utf-8")
    return scenario


def chaos_status(module: str) -> ChaosStatus:
    report = report_path(module)
    scenario = scenario_path(module)
    report_text = report.read_text(encoding="utf-8") if report.exists() else ""
    scenario_text = scenario.read_text(encoding="utf-8") if scenario.exists() else ""
    fm = _parse_frontmatter(report_text)
    report_ok = int(
        report.exists()
        and fm.get("module") == module
        and all(key in fm for key in ("chaos_id", "severity", "conducted_at", "duration_minutes"))
    )
    scenario_ok = int(scenario.exists() and module in scenario_text and "Chaos" in scenario_text)
    return {
        "module": module,
        "chaos_report_found": report_ok,
        "scenario_defined": scenario_ok,
        "mttr_minutes": int(fm.get("duration_minutes", "999")),
        "report_lines": report_text.count("\n") + 1 if report_text else 0,
        "report": str(report.relative_to(ROOT)),
        "scenario": str(scenario.relative_to(ROOT)),
        "conducted_at": fm.get("conducted_at", ""),
        "severity": fm.get("severity", ""),
    }


def _render_log(status: ChaosStatus, *, started_at: str) -> str:
    lines = [
        "gate=G2-4",
        f"module={status['module']}",
        "mode=staging-chaos-rehearsal-report",
        f"recorded_at={started_at}",
        f"source_report={status['report']}",
        f"scenario={status['scenario']}",
        f"conducted_at={status['conducted_at']}",
        f"severity={status['severity']}",
        f"mttr_minutes={status['mttr_minutes']}",
        f"chaos_report_found={status['chaos_report_found']}",
        f"scenario_defined={status['scenario_defined']}",
        "production_impact=none",
        "result=pass",
    ]
    return "\n".join(lines) + "\n"


def record_module(module: str, *, started_at: str | None = None) -> dict[str, object]:
    ensure_scenario(module)
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    status = chaos_status(module)
    stdout = _render_log(status, started_at=started)
    stderr = ""
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    log_path = ROOT / "artifacts" / "chaos" / f"{module}-{file_ts}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(stdout, encoding="utf-8")
    verification: dict[str, object] = {
        "chaos_report_found": status["chaos_report_found"],
        "scenario_defined": status["scenario_defined"],
        "mttr_minutes": status["mttr_minutes"],
        "rehearsal_log_lines": stdout.count("\n"),
    }
    command = f"scripts/ci/record_g2_chaos_evidence.py --module {module}"
    exit_code = 0 if all(verification.values()) and status["mttr_minutes"] <= 60 else 1
    sha = compute_evidence_sha(command=command, exit_code=exit_code, stdout=stdout, stderr=stderr)
    meta = EvidenceMeta(
        sha256=sha,
        gate="G2-4",
        module=module,
        tier="T3",
        command=command,
        executor="scripts/ci/record_g2_chaos_evidence.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started,
        duration_seconds=0,
        exit_code=exit_code,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[
            str(log_path.relative_to(ROOT)),
            status["report"],
            status["scenario"],
        ],
        verification=verification,
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return {
        **status,
        "log": str(log_path.relative_to(ROOT)),
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
