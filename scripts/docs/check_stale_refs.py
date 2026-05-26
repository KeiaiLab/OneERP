#!/usr/bin/env python3
"""삭제된 자산 참조와 죽은 마크다운 로컬 링크를 검출·교정하는 체커(S1).

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.1
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT_DEFAULT = Path(__file__).resolve().parents[2]

STALE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"docker-compose\.(local|plane)\.yml"),
    re.compile(r"\.gitea/"),
    re.compile(r"services/[^/\s`'\"]+/[^/\s`'\"]+/Dockerfile"),
    re.compile(r"scripts/migration/"),
    re.compile(r"devspace\.yaml"),
    re.compile(r"docs/HANDOFF-NEXT-SESSION\.md"),
    re.compile(r"docs/STATUS\.md"),
    re.compile(r"docs/gap-analysis-[\w-]+\.md"),
    re.compile(r"RALPH-LOOP-PROMPT\.md"),
    re.compile(r"AUDIT-REPORT-[\d-]+\.md"),
]

DOC_GLOBS = ["docs/**/*.md", "README.md", "AGENTS.md", ".claude/*.md"]
EXCLUDE_SUBSTR = [
    "docs/generated/",
    "node_modules/",
    ".venv/",
    ".worktrees/",
    ".git/",
    # superpowers spec/plan 문서는 체커·cleanup 스펙 자체이므로 패턴을 예시로 기재하는 것은 의도된 기록.
    "docs/superpowers/",
    # ADR 은 historical 결정문이라 과거 자산 언급이 의도된 기록.
    "docs/governance/adr/",
]

LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


@dataclass
class Finding:
    file: Path
    line: int
    kind: str  # "stale-ref" | "dead-link"
    detail: str


def _iter_target_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for pattern in DOC_GLOBS:
        for p in root.glob(pattern):
            if p.is_file() and not any(e in str(p) for e in EXCLUDE_SUBSTR):
                files.add(p)
    return sorted(files)


def _scan_stale(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for pat in STALE_PATTERNS:
            m = pat.search(line)
            if m:
                findings.append(
                    Finding(path, lineno, "stale-ref", m.group(0)),
                )
    return findings


def _scan_dead_links(path: Path, _root: Path) -> list[Finding]:
    findings: list[Finding] = []
    text = path.read_text(encoding="utf-8")
    for lineno, line in enumerate(text.splitlines(), start=1):
        for m in LINK_RE.finditer(line):
            target = m.group(2).strip()
            # 앵커, 외부 scheme, mailto, 이미지 절대경로는 스킵.
            if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
                continue
            # 앵커만 있는 경우(예: #section) 위에서 처리됨.
            target_path = target.split("#", 1)[0]
            if not target_path:
                continue
            # 상대 경로 기준으로 해석.
            resolved = (path.parent / target_path).resolve()
            if not resolved.exists():
                findings.append(
                    Finding(path, lineno, "dead-link", target),
                )
    return findings


def _fix_dead_links(path: Path, _root: Path) -> int:
    """죽은 링크를 plain 텍스트로 변환하고 교정 건수를 반환한다."""
    text = path.read_text(encoding="utf-8")
    fixed_count = 0

    def _repl(match: re.Match[str]) -> str:
        nonlocal fixed_count
        label, target = match.group(1), match.group(2).strip()
        if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
            return match.group(0)
        target_path = target.split("#", 1)[0]
        if not target_path:
            return match.group(0)
        resolved = (path.parent / target_path).resolve()
        if not resolved.exists():
            fixed_count += 1
            return label
        return match.group(0)

    new_text = LINK_RE.sub(_repl, text)
    if fixed_count > 0:
        path.write_text(new_text, encoding="utf-8")
    return fixed_count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="docs stale references + dead local links")
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--fix-dead-links", action="store_true")
    parser.add_argument("--fix", action="store_true", help="alias for --fix-dead-links")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    fix_mode = args.fix_dead_links or args.fix

    findings: list[Finding] = []
    for file in _iter_target_files(args.root):
        findings.extend(_scan_stale(file))
        findings.extend(_scan_dead_links(file, args.root))

    if fix_mode:
        total_fixed = 0
        for file in _iter_target_files(args.root):
            total_fixed += _fix_dead_links(file, args.root)
        print(f"[fix] dead-link 교정: {total_fixed} 건")
        # 재스캔하여 잔여 검출.
        findings = []
        for file in _iter_target_files(args.root):
            findings.extend(_scan_stale(file))
            findings.extend(_scan_dead_links(file, args.root))

    if args.json:
        import json

        payload = [
            {
                "file": str(f.file.relative_to(args.root)),
                "line": f.line,
                "kind": f.kind,
                "detail": f.detail,
            }
            for f in findings
        ]
        print(json.dumps(payload, ensure_ascii=False))
    else:
        for f in findings:
            rel = f.file.relative_to(args.root) if args.root in f.file.parents else f.file
            print(f"[{f.kind}] {rel}:{f.line} → {f.detail}")
        stale_cnt = sum(1 for f in findings if f.kind == "stale-ref")
        dead_cnt = sum(1 for f in findings if f.kind == "dead-link")
        print(f"총 {len(findings)} 건 감지 (stale-ref {stale_cnt}, dead-link {dead_cnt}).")

    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
