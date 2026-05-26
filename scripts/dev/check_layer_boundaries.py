"""Route → Service → Repository 3-layer 경계 위반 검출기.

M1-4 도입 (원칙 P2):
- `services/*/*/app/routes/*.py` 에서 `Repository(` 를 직접 호출하는 누수 감지
- `services/*/*/app/routes/*.py` 에서 `from oneerp_core.repository import` 감지
- `services/*/*/app/routes/*.py` 의 models/ 파일에서 Request/Response DTO 정의 감지
  (원칙 P4: models 에서 *Create/*Update/*Request/*Response 금지)

정책:
- `--check` 모드에서 **baseline(.arch-baseline.json) 이상** 증가 시 exit 1
- `--update-baseline` 으로 현재 위반 수를 baseline 에 저장 (감축 로드맵 상
  점진 감소를 반영)
- CI architecture-guards job 에서 `--check` 실행 (M4 에서 baseline=0 강제)
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TypedDict

ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / ".arch-baseline.json"
ROUTES_GLOB = "services/*/*/oneerp_*_app/routes/*.py"
MODELS_GLOB = "services/*/*/oneerp_*_app/models/*.py"
PLANE_GLOB = "planes/**/*.py"
WEB_GLOBS = [
    "web/app/**/*.ts*",
    "web/lib/**/*.ts*",
    "web/components/**/*.ts*",
    "web/tests/**/*.ts*",
]


class RuleSpec(TypedDict):
    paths: str | list[str]
    pattern: re.Pattern[str]
    desc: str


# OE001 등 번호는 로드맵의 원칙 식별자와 일치시킴
RULES: dict[str, RuleSpec] = {
    "OE002-route-direct-repo-instantiate": {
        "paths": ROUTES_GLOB,
        "pattern": re.compile(r"\bRepository\s*\("),
        "desc": "Route 에서 Repository(...) 직접 인스턴스화 금지 (P2)",
    },
    "OE002-route-import-repository": {
        "paths": ROUTES_GLOB,
        "pattern": re.compile(r"from oneerp_core\.repository import"),
        "desc": "Route 에서 oneerp_core.repository 직접 import 금지 (P2)",
    },
    "OE004-models-define-create-dto": {
        "paths": MODELS_GLOB,
        "pattern": re.compile(r"^\s*class\s+\w+(Create|Update|Request|Response)\b", re.MULTILINE),
        "desc": "models/ 에서 *Create/*Update/*Request/*Response DTO 정의 금지 — dto.py 로 격리 (P4)",
    },
    "OE101-plane-domain-rule-leak": {
        "paths": PLANE_GLOB,
        "pattern": re.compile(
            # plane 내 도메인 enum 직접 정의 금지
            r"class\s+\w+(?:Status|Type|Category|State)\s*\(\s*(?:(?:str|int)\s*,\s*)*(?:Enum|StrEnum|IntEnum)\b"
            # plane 내 도메인 비즈니스 상수 직접 정의 금지
            r"|(?:^|\s)(?:TAX_RATE|DISCOUNT_RATE|MARKUP_RATE|MARGIN_RATE|MAX_QTY|MIN_QTY)\s*[=:]",
            re.MULTILINE,
        ),
        "desc": "plane 에서 도메인 enum/비즈니스 상수 직접 정의 금지 — 해당 서비스로 이동 (OE101)",
    },
    "OE201-web-contract-bypass": {
        "paths": WEB_GLOBS,
        "pattern": re.compile(r"\bas any\b|:\s*any\b|<any>|Record<string,\s*any>"),
        "desc": "web route 에서 Any/dict 기반 계약 우회 금지",
    },
}


@dataclass
class Finding:
    rule: str
    path: str
    line: int


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)

    def count_by_rule(self) -> dict[str, int]:
        counts: dict[str, int] = dict.fromkeys(RULES, 0)
        for f in self.findings:
            counts[f.rule] = counts.get(f.rule, 0) + 1
        return counts


def _scan(rule: str, glob: str, pattern: re.Pattern[str]) -> list[Finding]:
    findings: list[Finding] = []
    for path in ROOT.glob(glob):
        if not path.is_file():
            continue
        rel = str(path.relative_to(ROOT))
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for m in pattern.finditer(text):
            line = text[: m.start()].count("\n") + 1
            findings.append(Finding(rule=rule, path=rel, line=line))
    return findings


def build_report() -> Report:
    r = Report()
    for rule, spec in RULES.items():
        paths: str | list[str] = spec["paths"]
        if isinstance(paths, str):
            paths = [paths]
        for glob in paths:
            r.findings.extend(_scan(rule, glob, spec["pattern"]))
    return r


def load_baseline() -> dict[str, int]:
    if BASELINE_PATH.exists():
        return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return dict.fromkeys(RULES, 0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="baseline 대비 증가 시 exit 1")
    parser.add_argument("--update-baseline", action="store_true", help="현재 값으로 baseline 갱신")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    report = build_report()
    counts = report.count_by_rule()

    print("=== Route → Service → Repository 경계 검사 ===")
    for rule, spec in RULES.items():
        print(f"  [{rule}] {counts[rule]}건 — {spec['desc']}")

    if args.verbose:
        print()
        print("=== 위반 상세 ===")
        for f in report.findings:
            print(f"  {f.path}:{f.line}  [{f.rule}]")

    if args.update_baseline:
        BASELINE_PATH.write_text(
            json.dumps(counts, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(f"\n→ baseline 갱신: {BASELINE_PATH.relative_to(ROOT)}")
        return 0

    if args.check:
        baseline = load_baseline()
        regressions = [
            f"  {rule}: {baseline.get(rule, 0)} → {counts[rule]}"
            for rule in RULES
            if counts[rule] > baseline.get(rule, 0)
        ]
        if regressions:
            print("\n❌ 경계 위반 증가 감지 (감소만 허용):")
            for r in regressions:
                print(r)
            return 1
        print("\n✓ baseline 대비 위반 증가 없음 (감소 또는 동일)")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
