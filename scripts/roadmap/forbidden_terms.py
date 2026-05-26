#!/usr/bin/env python3
"""로드맵 레이어 어휘 번짐 차단 CI.

각 md 문서의 frontmatter `audience` 를 읽어:
- audience: executive  → Executive 금지 어휘 스캔
- audience: engineering → Engineering 금지 어휘 스캔
- audience: shared    → 스캔 제외 (translation.md, matrix.md, glossary.md, status.md 등)

위반 1 건 이상 시 exit 1.

사용:
    python3 scripts/roadmap/forbidden_terms.py
    python3 scripts/roadmap/forbidden_terms.py --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROADMAP_DIR = REPO / "docs" / "product" / "roadmap"

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)
# 코드 블록(fenced), 마크다운 링크 전체, 프론트매터, HTML 주석, 자동 렌더 블록은 스캔 제외
FENCE_RE = re.compile(r"^```.*?^```", re.DOTALL | re.MULTILINE)
# 마크다운 링크 전체 `[text](url)` — 텍스트에도 경로/파일명이 자주 들어가므로 통째로 제거
LINK_FULL_RE = re.compile(r"\[[^\]]*\]\([^)]*\)")
HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
# 자동 렌더 블록 — 렌더러가 어휘 번짐을 책임진다
AUTO_EMBED_BLOCK_RE = re.compile(
    r"<!--\s*status-auto(?:-embed)?:[\w-]+\s*-->.*?<!--\s*/status-auto(?:-embed)?:[\w-]+\s*-->",
    re.DOTALL,
)

EXECUTIVE_FORBIDDEN = (
    r"\bPhase\b",
    r"\bphase\b",
    r"게이트",
    r"ADR-",
    r"pre-commercial",
    r"outbox",
    r"NATS",
    r"\bDoD\b",
    r"\bPlane\b",
    r"\bplane\b",
    # Wave/wave 는 허용 — 외부 문서도 쓰임. 대신 "모듈 집단" 을 권장.
)

ENGINEERING_FORBIDDEN = (
    r"경쟁\s*우위가",
    r"경쟁에서",
    r"이사회",
    r"투자자",
    r"고객\s*가치",
    r"제품\s*약속",
    r"북극성",
)


def read_audience(text: str) -> str | None:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return None
    match = re.search(r"^audience:\s*(\w+)", m.group(1), re.MULTILINE)
    return match.group(1) if match else None


def strip_scan_exclusions(text: str) -> str:
    """스캔에서 제외할 영역 제거. 라인 번호 보존을 위해 내용만 공백으로 치환."""

    def _blank(match: re.Match[str]) -> str:
        # 개행 수를 유지해 라인 번호가 어긋나지 않게 한다
        return "\n" * match.group(0).count("\n")

    # 자동 렌더 블록 제거 (최우선 — 렌더된 내용은 렌더러가 어휘 책임)
    text = AUTO_EMBED_BLOCK_RE.sub(_blank, text)
    # frontmatter 제거
    text = FRONTMATTER_RE.sub(_blank, text, count=1)
    # 코드 블록 제거
    text = FENCE_RE.sub(_blank, text)
    # 마크다운 링크 전체 제거 (URL + 링크 텍스트 모두)
    text = LINK_FULL_RE.sub(lambda m: " " * len(m.group(0)), text)
    # HTML 주석 제거
    return HTML_COMMENT_RE.sub(_blank, text)


def scan(text: str, patterns: tuple[str, ...]) -> list[tuple[int, str, str]]:
    """매칭된 (라인번호, 패턴, 매칭된 텍스트) 리스트."""
    findings: list[tuple[int, str, str]] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pat in patterns:
            findings.extend((lineno, pat, m.group(0)) for m in re.finditer(pat, line))
    return findings


def process_file(path: Path, *, verbose: bool) -> list[str]:
    text = path.read_text(encoding="utf-8")
    audience = read_audience(text)
    if audience in (None, "shared"):
        if verbose:
            sys.stdout.write(f"skip ({audience}): {path.relative_to(REPO)}\n")
        return []
    patterns = EXECUTIVE_FORBIDDEN if audience == "executive" else ENGINEERING_FORBIDDEN
    scannable = strip_scan_exclusions(text)
    findings = scan(scannable, patterns)
    if not findings:
        return []

    rel = path.relative_to(REPO)
    messages = [f"[{audience}] {rel}"]
    for lineno, pat, matched in findings:
        messages.append(f"  {rel}:{lineno} — 패턴 `{pat}` 매치: '{matched}'")
    return messages


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="어휘 번짐 CI 차단기")
    parser.add_argument("--verbose", action="store_true", help="스캔 스킵 파일도 출력")
    args = parser.parse_args(argv)

    total_violations = 0
    for path in sorted(ROADMAP_DIR.rglob("*.md")):
        messages = process_file(path, verbose=args.verbose)
        if messages:
            total_violations += len(messages) - 1  # 첫 줄은 헤더
            for line in messages:
                sys.stdout.write(line + "\n")

    if total_violations:
        sys.stderr.write(
            f"\n금지 어휘 위반 {total_violations} 건. translation.md 번역표로 대체하세요.\n"
        )
        return 1
    sys.stdout.write("금지 어휘 위반 없음.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
