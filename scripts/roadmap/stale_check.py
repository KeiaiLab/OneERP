#!/usr/bin/env python3
"""로드맵 문서 stale 배너 관리기.

각 md 문서의 frontmatter 에서 stale_after_days 를 읽어, git 마지막 커밋 시각 기준으로
TTL 을 초과한 문서의 본문 상단에 STALE 배너를 주입/갱신/제거한다.

사용:
    python3 scripts/roadmap/stale_check.py
    python3 scripts/roadmap/stale_check.py --warn-only   # 파일은 기록, exit 는 0
    python3 scripts/roadmap/stale_check.py --check       # diff 만 보고 기록하지 않음
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROADMAP_DIR = REPO / "docs" / "product" / "roadmap"

BANNER_RE = re.compile(
    r"^>\s*\*\*STALE.*?일\s*지남\*\*.*?\n(?:>.*?\n)*\n?",
    re.MULTILINE,
)
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def read_stale_ttl(text: str) -> int | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    match = re.search(r"^stale_after_days:\s*(\d+)", m.group(1), re.MULTILINE)
    return int(match.group(1)) if match else None


def last_commit_time(path: Path) -> datetime | None:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cI", "--", str(path)],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return None
    line = result.stdout.strip()
    if not line:
        return None
    try:
        return datetime.fromisoformat(line)
    except ValueError:
        return None


def compute_banner(last: datetime, ttl_days: int) -> str:
    days = (datetime.now(UTC) - last).days
    ymd = last.date().isoformat()
    return f"> **STALE — 마지막 갱신 {ymd}, {days}일 지남 (TTL {ttl_days}일)**\n\n"


def insert_or_replace_banner(text: str, banner: str) -> str:
    # 기존 배너 제거
    text = BANNER_RE.sub("", text, count=1)
    # frontmatter 뒤에 주입
    m = FRONTMATTER_RE.match(text)
    if not m:
        return banner + text
    pos = m.end()
    return text[:pos] + banner + text[pos:]


def remove_banner(text: str) -> str:
    return BANNER_RE.sub("", text, count=1)


def process_file(path: Path, *, check: bool) -> tuple[bool, str]:
    """파일 처리. 반환 (변경 여부, 상태 메시지)."""
    text = path.read_text(encoding="utf-8")
    ttl = read_stale_ttl(text)
    if ttl is None:
        return False, f"skip (no ttl): {path.relative_to(REPO)}"

    last = last_commit_time(path)
    if last is None:
        return False, f"skip (no git history): {path.relative_to(REPO)}"

    elapsed_days = (datetime.now(UTC) - last).days
    is_stale = elapsed_days > ttl

    if is_stale:
        banner = compute_banner(last, ttl)
        new_text = insert_or_replace_banner(text, banner)
        verdict = f"STALE ({elapsed_days}일 > TTL {ttl}일): {path.relative_to(REPO)}"
    else:
        new_text = remove_banner(text)
        verdict = f"fresh ({elapsed_days}일 ≤ TTL {ttl}일): {path.relative_to(REPO)}"

    changed = new_text != text
    if changed and not check:
        path.write_text(new_text, encoding="utf-8")
    return changed, verdict


def iter_targets() -> list[Path]:
    return sorted(ROADMAP_DIR.rglob("*.md"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="로드맵 stale 배너 관리")
    parser.add_argument("--check", action="store_true", help="diff 만 보고 기록하지 않음")
    parser.add_argument("--warn-only", action="store_true", help="stale 발견해도 exit 0")
    args = parser.parse_args(argv)

    any_stale = False
    total_changed = 0
    for path in iter_targets():
        changed, verdict = process_file(path, check=args.check)
        if changed:
            total_changed += 1
        if "STALE" in verdict:
            any_stale = True
            sys.stdout.write(verdict + "\n")

    sys.stdout.write(f"stale 문서 반영 {total_changed} 건\n")
    if any_stale and not args.warn_only:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
