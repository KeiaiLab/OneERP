#!/usr/bin/env python3
"""문서 로컬 링크와 인덱스 도달성을 검증한다."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

IGNORED_PARTS = {
    ".git",
    ".venv",
    ".worktrees",
    "node_modules",
    "artifacts",
    "__pycache__",
}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
INLINE_CODE_RE = re.compile(r"`[^`\n]*`")


@dataclass(frozen=True)
class BrokenLink:
    source: str
    target: str


@dataclass(frozen=True)
class IntegrityReport:
    seed: str
    broken_links: list[BrokenLink]
    unreachable_docs: list[str]


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        if any(part in IGNORED_PARTS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def strip_code(text: str) -> str:
    lines: list[str] = []
    in_fence = False
    fence_marker = ""

    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
                fence_marker = ""
            continue
        if not in_fence:
            lines.append(line)

    return INLINE_CODE_RE.sub("", "".join(lines))


def resolve_local_target(source: Path, raw_target: str) -> Path | None:
    target = raw_target.strip()
    if not target or target.startswith(("http://", "https://", "mailto:", "#")):
        return None

    target = target.split("#", 1)[0]
    if not target:
        return None

    return (source.parent / target).resolve()


def build_integrity_report(root: Path, seed: str = "docs/INDEX.md") -> IntegrityReport:
    root = root.resolve()
    markdown_files = iter_markdown_files(root)
    doc_map = {str(path.relative_to(root)): path for path in markdown_files}
    graph = {rel: set() for rel in doc_map}
    broken_links: list[BrokenLink] = []

    for rel_path, abs_path in doc_map.items():
        content = strip_code(abs_path.read_text(encoding="utf-8"))
        for raw_target in LINK_RE.findall(content):
            resolved = resolve_local_target(abs_path, raw_target)
            if resolved is None:
                continue

            try:
                resolved_rel = str(resolved.relative_to(root))
            except ValueError:
                continue

            if not resolved.exists():
                broken_links.append(BrokenLink(source=rel_path, target=raw_target))
                continue

            if resolved_rel in graph:
                graph[rel_path].add(resolved_rel)

    seen: set[str] = set()
    stack = [seed] if seed in graph else []
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack.extend(sorted(graph[current] - seen, reverse=True))

    unreachable_docs = sorted(
        rel_path for rel_path in doc_map if rel_path.startswith("docs/") and rel_path not in seen
    )
    broken_links.sort(key=lambda item: (item.source, item.target))
    return IntegrityReport(
        seed=seed,
        broken_links=broken_links,
        unreachable_docs=unreachable_docs,
    )


def print_report(report: IntegrityReport) -> None:
    print("=== 문서 무결성 검사 ===")
    print(f"기준 인덱스: {report.seed}")
    print(f"깨진 로컬 링크: {len(report.broken_links)}건")
    if report.broken_links:
        for item in report.broken_links:
            print(f"  - {item.source} -> {item.target}")

    print(f"고아 문서: {len(report.unreachable_docs)}건")
    if report.unreachable_docs:
        for rel_path in report.unreachable_docs:
            print(f"  - {rel_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="문서 무결성 검사")
    parser.add_argument(
        "--seed",
        default="docs/INDEX.md",
        help="도달성 계산의 시작 문서",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = build_integrity_report(Path.cwd(), seed=args.seed)
    print_report(report)
    return 1 if report.broken_links or report.unreachable_docs else 0


if __name__ == "__main__":
    raise SystemExit(main())
