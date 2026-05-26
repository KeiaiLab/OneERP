#!/usr/bin/env python3
"""로드맵 링크 검증 — forward(깨진 경로) + reverse(SoT → 로드맵 역참조).

두 모드:
  --forward : docs/product/roadmap/ 내부 md 의 상대/절대 링크가 실제 파일을 가리키는지
  --reverse : .planning/·docs/governance/·docs/engineering/·docs/infra/·docs/ops/ 등에서
              docs/product/roadmap/ 경로를 인용하는지 (역참조는 SoT 단방향 원칙 위반)

사용:
    python3 scripts/roadmap/link_check.py --forward --reverse
    python3 scripts/roadmap/link_check.py --forward
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROADMAP_DIR = REPO / "docs" / "product" / "roadmap"
REVERSE_SCAN_DIRS = (
    REPO / ".planning",
    REPO / "docs" / "governance",
    REPO / "docs" / "engineering",
    REPO / "docs" / "infra",
    REPO / "docs" / "ops",
    REPO / "docs" / "api",
    REPO / "docs" / "plans",
)
# 역참조 스캔에서 제외할 경로.
# .planning/phases/ 와 docs/plans/ 의 실행 계획은 "로드맵 파일을 업데이트하라" 는
# Task 를 정당하게 포함할 수 있다 (정본/facts 이 아닌 실행계획/actions).
# 로드맵 문서 자체는 업데이트될 수 있지만 인용 방향은 여전히 단방향 유지.
REVERSE_EXCLUDES = (
    REPO / ".planning" / "phases",
    REPO / "docs" / "plans",
)

LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#]+)(?:#[^)]*)?\)")
ROADMAP_REF_RE = re.compile(r"docs/product/roadmap/")


def _is_excluded(md: Path) -> bool:
    return any(md.is_relative_to(ex) for ex in REVERSE_EXCLUDES)


def check_forward(*, verbose: bool) -> list[str]:
    errors: list[str] = []
    for md in sorted(ROADMAP_DIR.rglob("*.md")):
        text = md.read_text(encoding="utf-8")
        for m in LINK_RE.finditer(text):
            target_raw = m.group(1).strip()
            if not target_raw:
                continue
            if target_raw.startswith(("http://", "https://", "mailto:")):
                continue
            if target_raw.startswith("#"):
                continue
            target = (md.parent / target_raw).resolve()
            if not target.exists():
                rel = md.relative_to(REPO)
                errors.append(f"[forward] {rel} → 존재하지 않음: {target_raw}")
        if verbose:
            sys.stdout.write(f"scanned {md.relative_to(REPO)}\n")
    return errors


def check_reverse(*, verbose: bool) -> list[str]:
    errors: list[str] = []
    for root in REVERSE_SCAN_DIRS:
        if not root.exists():
            continue
        for md in sorted(root.rglob("*.md")):
            if _is_excluded(md):
                if verbose:
                    sys.stdout.write(f"skipped (excluded) {md.relative_to(REPO)}\n")
                continue
            try:
                text = md.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for lineno, line in enumerate(text.splitlines(), start=1):
                if ROADMAP_REF_RE.search(line):
                    rel = md.relative_to(REPO)
                    errors.append(
                        f"[reverse] {rel}:{lineno} — SoT 파일이 로드맵을 인용함: '{line.strip()}'"
                    )
            if verbose:
                sys.stdout.write(f"scanned {md.relative_to(REPO)}\n")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="로드맵 링크 검증")
    parser.add_argument("--forward", action="store_true", help="로드맵 내 링크 검증")
    parser.add_argument("--reverse", action="store_true", help="SoT → 로드맵 역참조 검증")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    if not (args.forward or args.reverse):
        args.forward = True
        args.reverse = True

    errors: list[str] = []
    if args.forward:
        errors.extend(check_forward(verbose=args.verbose))
    if args.reverse:
        errors.extend(check_reverse(verbose=args.verbose))

    if errors:
        for e in errors:
            sys.stdout.write(e + "\n")
        sys.stderr.write(f"\n링크 위반 {len(errors)} 건.\n")
        return 1
    sys.stdout.write("링크 위반 없음.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
