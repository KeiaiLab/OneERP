#!/usr/bin/env python3
"""메모리/CPU 회귀 탐지 공용 스크립트 — G2-3 게이트.

CI 또는 로컬에서 모듈별 벤치마크 baseline 과 현재 측정값을 비교해
허용 범위를 벗어나는 회귀를 자동 감지한다.

baseline 파일: `docs/engineering/data/perf-<module>-baseline.json`
측정 결과: `scripts/perf/<module>-latest.json` (CI 가 생성)

사용:
    uv run python scripts/perf/regression.py --module gateway --threshold 15
    uv run python scripts/perf/regression.py --all --format json
    uv run python scripts/perf/regression.py --module accounting --baseline-update  # baseline 갱신 (CI 승격 시)

허용 범위:
  - p95 latency: +15% 초과 시 회귀
  - RSS memory: +20% 초과 시 회귀
  - CPU user: +25% 초과 시 회귀

종료 코드:
  0 — 회귀 없음
  1 — 회귀 감지 (하나 이상 지표 임계치 초과)
  2 — 환경 오류 (baseline 또는 latest 파일 없음)
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
BASELINE_DIR = REPO / "docs/engineering/data"
LATEST_DIR = REPO / "scripts/perf"

DEFAULT_THRESHOLDS: dict[str, float] = {
    "p95_latency_ms": 15.0,
    "rss_memory_mb": 20.0,
    "cpu_user_pct": 25.0,
}


@dataclass
class RegressionFinding:
    metric: str
    baseline: float
    current: float
    delta_pct: float
    threshold_pct: float

    @property
    def is_regression(self) -> bool:
        return self.delta_pct > self.threshold_pct


def _load_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError, json.JSONDecodeError:
        return None


def compare(module: str, thresholds: dict[str, float]) -> tuple[list[RegressionFinding], bool]:
    baseline = _load_json(BASELINE_DIR / f"perf-{module}-baseline.json")
    current = _load_json(LATEST_DIR / f"{module}-latest.json")
    if baseline is None or current is None:
        return [], False
    findings: list[RegressionFinding] = []
    for metric, threshold in thresholds.items():
        b = baseline.get(metric)
        c = current.get(metric)
        if b is None or c is None or b == 0:
            continue
        delta = 100.0 * (c - b) / b
        findings.append(
            RegressionFinding(
                metric=metric,
                baseline=float(b),
                current=float(c),
                delta_pct=delta,
                threshold_pct=threshold,
            ),
        )
    return findings, True


def update_baseline(module: str) -> bool:
    """현재 측정값을 baseline 으로 승격."""
    latest = _load_json(LATEST_DIR / f"{module}-latest.json")
    if latest is None:
        return False
    BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    (BASELINE_DIR / f"perf-{module}-baseline.json").write_text(
        json.dumps(latest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return True


def _report_text(module: str, findings: list[RegressionFinding]) -> str:
    lines = [f"module: {module}"]
    if not findings:
        lines.append("  (no comparable data — baseline or latest missing)")
        return "\n".join(lines)
    for f in findings:
        marker = "!! REGRESSION" if f.is_regression else "ok"
        lines.append(
            f"  [{marker:13s}] {f.metric:20s} "
            f"baseline={f.baseline:.2f} current={f.current:.2f} "
            f"Δ={f.delta_pct:+.1f}% (threshold {f.threshold_pct:+.1f}%)",
        )
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="성능 회귀 탐지 (G2-3)")
    target = p.add_mutually_exclusive_group(required=True)
    target.add_argument("--module", help="단일 모듈 검사")
    target.add_argument("--all", action="store_true", help="BASELINE_DIR 의 모든 모듈")
    p.add_argument("--threshold-latency", type=float, default=DEFAULT_THRESHOLDS["p95_latency_ms"])
    p.add_argument("--threshold-memory", type=float, default=DEFAULT_THRESHOLDS["rss_memory_mb"])
    p.add_argument("--threshold-cpu", type=float, default=DEFAULT_THRESHOLDS["cpu_user_pct"])
    p.add_argument("--baseline-update", action="store_true")
    p.add_argument("--format", choices=["text", "json"], default="text")
    args = p.parse_args()

    thresholds = {
        "p95_latency_ms": args.threshold_latency,
        "rss_memory_mb": args.threshold_memory,
        "cpu_user_pct": args.threshold_cpu,
    }

    if args.all:
        modules = sorted(
            m.stem.removeprefix("perf-").removesuffix("-baseline")
            for m in BASELINE_DIR.glob("perf-*-baseline.json")
        )
    else:
        modules = [args.module]

    if args.baseline_update:
        ok = all(update_baseline(m) for m in modules)
        print(f"baseline updated: {len(modules)} modules" if ok else "ERROR: some latest missing")
        return 0 if ok else 2

    any_regression = False
    results: list[dict] = []
    for m in modules:
        findings, ok = compare(m, thresholds)
        if not ok:
            print(f"{m}: SKIP — missing baseline or latest", file=sys.stderr)
            continue
        regs = [f for f in findings if f.is_regression]
        if regs:
            any_regression = True
        if args.format == "text":
            print(_report_text(m, findings))
        else:
            results.append(
                {
                    "module": m,
                    "findings": [
                        {
                            "metric": f.metric,
                            "baseline": f.baseline,
                            "current": f.current,
                            "delta_pct": f.delta_pct,
                            "is_regression": f.is_regression,
                        }
                        for f in findings
                    ],
                },
            )

    if args.format == "json":
        print(
            json.dumps(
                {"results": results, "any_regression": any_regression}, ensure_ascii=False, indent=2
            )
        )

    return 1 if any_regression else 0


if __name__ == "__main__":
    raise SystemExit(main())
