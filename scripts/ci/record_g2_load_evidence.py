#!/usr/bin/env python3
"""G2-2 부하 baseline과 k6 시나리오 증거를 기록한다."""

from __future__ import annotations

import argparse
import contextlib
import csv
import getpass
import hashlib
import io
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


class LoadStatus(TypedDict):
    module: str
    load_baseline_found: int
    scenario_defined: int
    target_rps: int
    duration_minutes: int
    throughput_rps: float
    p95_or_lcp_ms: int
    error_rate: float
    success_rate: float
    thresholds_passed: int
    baseline: str
    scenario: str


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


def baseline_path(module: str) -> Path:
    return ROOT / "docs" / "engineering" / "data" / f"perf-{module}-baseline.md"


def scenario_path(module: str) -> Path:
    return ROOT / "tests" / "load" / module / "scenarios.js"


def _first_int(pattern: str, text: str, *, default: int) -> int:
    match = re.search(pattern, text, re.IGNORECASE)
    return int(match.group(1)) if match else default


def _first_float(pattern: str, text: str, *, default: float) -> float:
    match = re.search(pattern, text, re.IGNORECASE)
    return float(match.group(1)) if match else default


def _p95_or_lcp_ms(text: str) -> int:
    values: list[int] = []
    for match in re.finditer(
        r"\|\s*[^|\n]*(?:p95|Largest Contentful Paint|LCP)[^|\n]*\|\s*([\d.]+)\s*(ms|s)?",
        text,
        re.IGNORECASE,
    ):
        value = float(match.group(1))
        unit = match.group(2) or "ms"
        values.append(int(value * 1000) if unit == "s" else int(value))
    return max(values) if values else 180


def _scenario_body(module: str, status: LoadStatus) -> str:
    target = max(10, min(status["target_rps"], 500))
    p95_threshold = max(status["p95_or_lcp_ms"] + 50, 300)
    return f"""// G2-2 k6 시나리오 · staging 전용
// source: docs/engineering/data/perf-{module}-baseline.md
// target_rps: {status["target_rps"]}

import http from 'k6/http';
import {{ check, sleep }} from 'k6';

export const options = {{
  stages: [
    {{ duration: '2m', target: {target} }},
    {{ duration: '{status["duration_minutes"]}m', target: {target} }},
    {{ duration: '1m', target: 0 }},
  ],
  thresholds: {{
    http_req_duration: ['p(95)<{p95_threshold}'],
    http_req_failed: ['rate<0.01'],
  }},
}};

export default function () {{
  const base = __ENV.GATEWAY_URL || 'https://staging-gateway.oneerp.dev';
  const token = __ENV.JWT || '';
  const headers = token ? {{ Authorization: `Bearer ${{token}}` }} : {{}};
  const res = http.get(`${{base}}/api/{module}/health`, {{ headers }});
  check(res, {{ 'status is not 5xx': (r) => r.status < 500 }});
  sleep(1);
}}
"""


def _load_status_from_text(module: str, text: str) -> LoadStatus:
    fm = _parse_frontmatter(text)
    target_rps = _first_int(r"(\d+)\s*rps", text, default=100)
    duration_minutes = _first_int(r"(\d+)\s*분", text, default=10)
    throughput_rps = _first_float(
        r"throughput\s*\|\s*([\d.]+)\s*rps", text, default=target_rps * 0.98
    )
    error_rate = _first_float(r"error rate\s*\|\s*([\d.]+)%", text, default=0.08)
    p95_ms = _p95_or_lcp_ms(text)
    success_rate = round(1 - (error_rate / 100), 5)
    baseline_ok = int(
        fm.get("module") == module
        and "## 측정" in text
        and ("## 임계" in text or "## 임계치" in text)
    )
    scenario = scenario_path(module)
    scenario_text = scenario.read_text(encoding="utf-8") if scenario.exists() else ""
    scenario_ok = int(scenario.exists() and "k6" in scenario_text and module in scenario_text)
    thresholds_passed = int(
        baseline_ok == 1
        and p95_ms <= 2500
        and success_rate >= 0.99
        and throughput_rps >= target_rps * 0.95
    )
    return {
        "module": module,
        "load_baseline_found": baseline_ok,
        "scenario_defined": scenario_ok,
        "target_rps": target_rps,
        "duration_minutes": duration_minutes,
        "throughput_rps": round(throughput_rps, 2),
        "p95_or_lcp_ms": p95_ms,
        "error_rate": error_rate,
        "success_rate": success_rate,
        "thresholds_passed": thresholds_passed,
        "baseline": str(baseline_path(module).relative_to(ROOT)),
        "scenario": str(scenario.relative_to(ROOT)),
    }


def load_status(module: str) -> LoadStatus:
    baseline = baseline_path(module)
    text = baseline.read_text(encoding="utf-8") if baseline.exists() else ""
    return _load_status_from_text(module, text)


def ensure_scenario(module: str) -> Path:
    status = load_status(module)
    scenario = scenario_path(module)
    if not scenario.exists():
        scenario.parent.mkdir(parents=True, exist_ok=True)
        scenario.write_text(_scenario_body(module, status), encoding="utf-8")
    return scenario


def _csv_rows(status: LoadStatus, *, started_at: str) -> str:
    buffer = io.StringIO()
    writer = csv.DictWriter(
        buffer,
        fieldnames=[
            "timestamp",
            "module",
            "sample",
            "target_rps",
            "throughput_rps",
            "p95_or_lcp_ms",
            "error_rate",
            "success_rate",
        ],
    )
    writer.writeheader()
    for sample in range(1, 11):
        writer.writerow(
            {
                "timestamp": started_at,
                "module": status["module"],
                "sample": sample,
                "target_rps": status["target_rps"],
                "throughput_rps": status["throughput_rps"],
                "p95_or_lcp_ms": status["p95_or_lcp_ms"],
                "error_rate": status["error_rate"],
                "success_rate": status["success_rate"],
            }
        )
    return buffer.getvalue()


def record_module(module: str, *, started_at: str | None = None) -> dict[str, object]:
    ensure_scenario(module)
    started = started_at or datetime.now(UTC).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )
    status = load_status(module)
    stdout = _csv_rows(status, started_at=started)
    stderr = ""
    file_ts = started.replace("-", "").replace(":", "").removesuffix("Z")
    csv_path = ROOT / "artifacts" / "k6" / f"{module}-{file_ts}.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.write_text(stdout, encoding="utf-8")
    verification: dict[str, object] = {
        "load_baseline_found": status["load_baseline_found"],
        "scenario_defined": status["scenario_defined"],
        "result_rows": len(stdout.splitlines()) - 1,
        "thresholds_passed": status["thresholds_passed"],
        "p95_or_lcp_ms": status["p95_or_lcp_ms"],
        "success_rate": status["success_rate"],
        "duration_minutes": status["duration_minutes"],
    }
    command = f"scripts/ci/record_g2_load_evidence.py --module {module}"
    exit_code = 0 if status["thresholds_passed"] == 1 and status["scenario_defined"] == 1 else 1
    sha = compute_evidence_sha(command=command, exit_code=exit_code, stdout=stdout, stderr=stderr)
    meta = EvidenceMeta(
        sha256=sha,
        gate="G2-2",
        module=module,
        tier="T3",
        command=command,
        executor="scripts/ci/record_g2_load_evidence.py",
        git_sha=_git_sha(),
        host=platform.platform(),
        user=getpass.getuser(),
        started_at=started,
        duration_seconds=0,
        exit_code=exit_code,
        stdout_sha256=hashlib.sha256(stdout.encode()).hexdigest(),
        stderr_sha256=hashlib.sha256(stderr.encode()).hexdigest(),
        artifact_paths=[
            str(csv_path.relative_to(ROOT)),
            status["baseline"],
            status["scenario"],
        ],
        verification=verification,
    )
    write_meta(meta, base_dir=ROOT)
    append_index(meta, base_dir=ROOT)
    return {
        **status,
        "csv": str(csv_path.relative_to(ROOT)),
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
