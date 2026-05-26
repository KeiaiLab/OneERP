#!/usr/bin/env python3
"""docs/**/*.md frontmatter 최소 스키마 검증기.

정책:
  - frontmatter(`---` 블록) 가 없는 문서는 스킵 (현 시점엔 소수 문서만 frontmatter 보유)
  - frontmatter 가 있으면 key=value 행으로 단순 파싱 가능해야 함
  - `role` 이 있으면 허용 enum 값이어야 함
  - `status` 가 있으면 허용 enum 값이어야 함
  - `last_updated` 가 있으면 ISO 8601 (YYYY-MM-DD) 형식이어야 함

사용:
  python3 scripts/docs/validate_frontmatter.py           # warn-only
  python3 scripts/docs/validate_frontmatter.py --strict  # 1 이상 위반 시 exit 1
"""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = ROOT / "docs"
SKIP_DIRS = {".git", ".venv", ".worktrees", "node_modules", "archive", "generated", "__pycache__"}

VALID_ROLES = {"sot", "gsd_state", "spec", "guide", "reference", "archive", "generated"}
VALID_STATUSES = {"active", "deprecated", "in_progress", "archived", "draft"}

FM_PATTERN = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}")


def _iter_markdown(root: Path):
    for p in root.rglob("*.md"):
        parts = set(p.relative_to(ROOT).parts)
        if parts & SKIP_DIRS:
            continue
        yield p


def _extract_top_level(fm: str) -> dict[str, str]:
    """들여쓰기 없는 최상위 key=value 만 수집 (simple YAML subset)."""
    out: dict[str, str] = {}
    for line in fm.splitlines():
        if not line or line[0].isspace() or line.startswith("#"):
            continue
        m = re.match(r"([A-Za-z_][\w_]*):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip("\"'")
    return out


def check_file(path: Path) -> list[str]:
    issues: list[str] = []
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = FM_PATTERN.match(text)
    if not m:
        return issues

    fm_raw = m.group(1)
    fields = _extract_top_level(fm_raw)

    rel = path.relative_to(ROOT)

    if "role" in fields and fields["role"] not in VALID_ROLES:
        issues.append(f"{rel}: role='{fields['role']}' (허용: {sorted(VALID_ROLES)})")

    if "status" in fields and fields["status"] not in VALID_STATUSES:
        issues.append(f"{rel}: status='{fields['status']}' (허용: {sorted(VALID_STATUSES)})")

    if "last_updated" in fields:
        val = fields["last_updated"]
        if not DATE_PATTERN.match(val):
            issues.append(f"{rel}: last_updated='{val}' (YYYY-MM-DD 형식 필요)")
        else:
            try:
                date.fromisoformat(val[:10])
            except ValueError:
                issues.append(f"{rel}: last_updated='{val}' 파싱 실패")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="위반 시 exit 1")
    args = parser.parse_args()

    all_issues: list[str] = []
    count_with_fm = 0
    count_total = 0

    for path in _iter_markdown(DOCS_DIR):
        count_total += 1
        text = path.read_text(encoding="utf-8", errors="ignore")
        if FM_PATTERN.match(text):
            count_with_fm += 1
        issues = check_file(path)
        all_issues.extend(issues)

    if all_issues:
        print("=== frontmatter 위반 ===")
        for issue in all_issues:
            print(f"  △ {issue}")
    else:
        print("✓ frontmatter 위반 없음")

    print(f"\n스캔 {count_total}개 / frontmatter 보유 {count_with_fm}개 / 위반 {len(all_issues)}개")

    if args.strict and all_issues:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
