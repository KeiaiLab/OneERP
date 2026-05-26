#!/usr/bin/env python3
"""웨이브 진입 조건 점검기 (ADR-0012 §6 · §10).

- 활성 웨이브를 판정하고, 진입 조건·완료 조건 충족 여부를 표시한다.
- 상용 게이트 점검기(`commercial_readiness.py`)의 결과를 흡수해 웨이브 단위로 집계.

사용:
    uv run --package oneerp-core python scripts/audit/wave_entry_check.py
    uv run --package oneerp-core python scripts/audit/wave_entry_check.py --wave 1
    uv run --package oneerp-core python scripts/audit/wave_entry_check.py --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "audit"))

_commercial_readiness = import_module("commercial_readiness")
Label = _commercial_readiness.Label
discover_modules = _commercial_readiness.discover_modules
run_module = _commercial_readiness.run_module

# ---------------------------------------------------------------------------
# ADR-0012 §2 웨이브 분류 (47 모듈)
# ---------------------------------------------------------------------------
WAVES: dict[int, list[str]] = {
    1: [
        "gateway",
        "directory",
        "accounting",
        "hr",
        "payroll",
        "selling",
        "buying",
        "stock",
        "expenses",
        "projects",
        "crm",
        "portal",
    ],
    2: [
        "manufacturing",
        "quality",
        "assets",
        "maintenance",
        "ecommerce",
        "pos",
        "subscriptions",
        "integration-hub",
        "calendar",
        "documents",
        "mail",
        "messenger",
        "board",
    ],
    3: [
        "consolidation",
        "esg",
        "compliance",
        "clm",
        "ehs",
        "plm",
        "tms",
        "fleet",
        "advanced-planning",
        "marketing",
        "marketing-automation",
        "gtm",
        "lms",
        "workreport",
    ],
    4: [
        "analytics",
        "rpa",
        "iot",
        "knowledge",
        "wiki",
        "survey",
        "reservation",
        "rental",
    ],
}

# ADR-0012 §6 웨이브별 완료 조건 — "commercial-ready" 강제 모듈
COMMERCIAL_REQUIRED: dict[int, list[str]] = {
    1: ["selling", "buying", "stock", "accounting"],  # Starter 플랜
    2: [],  # Business 플랜 — 모든 Wave 2 commercial-ready (리스트 생략)
    3: [],
    4: [],  # Wave 4는 beta 이상만 요구
}

# ADR-0012 §6 진입 조건 — 간단 점검 가능한 항목만 (infra 가동 등 수동 확인 필요 항목 제외)
ENTRY_CHECKS: dict[int, list[str]] = {
    1: [
        "ADR-0008 관측성 인프라 가동 (Prometheus/Loki/Tempo) — 수동",
        "ADR-0006 authorize() 코어 구현 — 수동",
        "ADR-0005 TenantScopedRepository 강제 — 수동",
    ],
    2: ["Wave 1 전수 pre-commercial+"],
    3: ["Wave 2 전수 pre-commercial+"],
    4: ["Wave 3 전수 pre-commercial+", "ADR-0007 v1 stable"],
}


@dataclass
class WaveStatus:
    wave: int
    modules: list[str]
    label_counts: dict[str, int] = field(default_factory=dict)
    pre_commercial_or_better: int = 0
    commercial_ready: int = 0
    commercial_required_met: bool = False
    entry_conditions_met: bool = False  # 하위 웨이브 전수 완료 여부

    @property
    def exit_complete(self) -> bool:
        """ADR-0012 §6 완료 조건. 모든 대상 모듈이 23/23일 때만 완료."""
        return self.commercial_ready == len(self.modules) and self.commercial_required_met


def _label_ge(actual: str, threshold: Label) -> bool:
    order = [Label.ALPHA, Label.BETA, Label.PRE_COMMERCIAL, Label.COMMERCIAL_READY]
    idx = {lbl.value: i for i, lbl in enumerate(order)}
    return idx[actual] >= idx[threshold.value]


def assess_wave(wave: int, all_reports: dict[str, Label]) -> WaveStatus:
    mods = WAVES[wave]
    status = WaveStatus(wave=wave, modules=mods)
    status.label_counts = {lbl.value: 0 for lbl in Label}
    for m in mods:
        lbl = all_reports.get(m, Label.ALPHA.value)
        status.label_counts[lbl] += 1
        if _label_ge(lbl, Label.PRE_COMMERCIAL):
            status.pre_commercial_or_better += 1
        if lbl == Label.COMMERCIAL_READY.value:
            status.commercial_ready += 1
    required = COMMERCIAL_REQUIRED.get(wave, [])
    if required:
        status.commercial_required_met = all(
            all_reports.get(m) == Label.COMMERCIAL_READY.value for m in required
        )
    else:
        status.commercial_required_met = True  # 요구 목록 없음
    return status


def determine_active_wave(waves: list[WaveStatus]) -> int:
    """활성 웨이브 = 이전 웨이브 완료 + 현재 웨이브 미완료."""
    for w in waves:
        if not w.exit_complete:
            return w.wave
    return waves[-1].wave  # 전부 완료


def render_markdown(waves: list[WaveStatus], active: int) -> str:
    lines = [
        "# 웨이브 진입/완료 현황 (자동 생성)",
        "",
        "> 근거: ADR-0012 §2 웨이브 분류 + §6 진입/완료 조건 + §10 실행 항목.",
        "> 생성: `scripts/audit/wave_entry_check.py`.",
        "",
        f"**활성 웨이브: Wave {active}**",
        "",
        "## 웨이브별 상태",
        "",
        "| Wave | 모듈 수 | pre-commercial+ | commercial-ready | 진입? | 완료? |",
        "|------|---------|------------------|-------------------|-------|--------|",
    ]
    for w in waves:
        entry = "✅" if w.wave == 1 or (w.wave > 1 and waves[w.wave - 2].exit_complete) else "⏳"
        done = "✅" if w.exit_complete else "❌"
        lines.append(
            f"| Wave {w.wave} | {len(w.modules)} | "
            f"{w.pre_commercial_or_better}/{len(w.modules)} | "
            f"{w.commercial_ready}/{len(w.modules)} | {entry} | {done} |"
        )
    lines.append("")
    for w in waves:
        lines.append(f"### Wave {w.wave}")
        counts = w.label_counts
        lines.append(
            f"- 라벨 분포: alpha={counts['alpha']} / beta={counts['beta']} / "
            f"pre-commercial={counts['pre-commercial']} / "
            f"commercial-ready={counts['commercial-ready']}"
        )
        required = COMMERCIAL_REQUIRED.get(w.wave, [])
        if required:
            status = "✅" if w.commercial_required_met else "❌"
            lines.append(
                f"- 필수 commercial-ready 모듈({status}): " + ", ".join(required),
            )
        lines.append("- 진입 조건 체크리스트(수동 포함):")
        lines.extend(f"  - [ ] {c}" for c in ENTRY_CHECKS.get(w.wave, []))
        lines.append("- 모듈 라벨:")
        lines.extend(f"  - `{m}` — (현재 라벨은 commercial_readiness.py 참조)" for m in w.modules)
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    p = argparse.ArgumentParser(description="웨이브 진입/완료 점검 (ADR-0012)")
    p.add_argument("--wave", type=int, choices=[1, 2, 3, 4], help="특정 웨이브만 표시")
    p.add_argument("--format", choices=["summary", "markdown", "json"], default="summary")
    args = p.parse_args()

    # commercial_readiness.py를 직접 호출해 47 모듈 라벨 수집
    all_modules = discover_modules()
    reports = {m: run_module(m).label().value for m in all_modules}

    wave_ids = [args.wave] if args.wave else [1, 2, 3, 4]
    waves = [assess_wave(w, reports) for w in wave_ids]
    active = determine_active_wave(waves)

    if args.format == "json":
        print(
            json.dumps(
                {
                    "active_wave": active,
                    "waves": [
                        {
                            "wave": w.wave,
                            "modules": w.modules,
                            "labels": w.label_counts,
                            "pre_commercial_or_better": w.pre_commercial_or_better,
                            "commercial_ready": w.commercial_ready,
                            "exit_complete": w.exit_complete,
                        }
                        for w in waves
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.format == "markdown":
        print(render_markdown(waves, active))
    else:  # summary
        print(f"활성 웨이브: Wave {active}")
        print()
        for w in waves:
            bar = "█" * w.commercial_ready + "░" * (len(w.modules) - w.commercial_ready)
            status_mark = "✅" if w.exit_complete else "⏳"
            print(
                f"  Wave {w.wave} {status_mark}  "
                f"{w.commercial_ready:2d}/{len(w.modules):2d}  "
                f"[{bar}]  "
                f"(commercial-ready: {w.commercial_ready})"
            )
        print()
        print("진입/완료 세부는 --format markdown 또는 --format json")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
