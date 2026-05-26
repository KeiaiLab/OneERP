#!/usr/bin/env python3
"""ARCHITECTURE-MAP/CONSOLIDATION 등 구조 문서와 현 코드 기반 실측 집합 비교(S5).

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.5
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

import yaml

ROOT_DEFAULT = Path(__file__).resolve().parents[2]

TARGET_DOCS_DEFAULT = [
    "docs/ARCHITECTURE-MAP.md",
    "docs/engineering/msa/CONSOLIDATION.md",
]
ADR_GLOB = "docs/governance/adr/*.md"

TOKEN_RE = re.compile(r"`([a-z][a-z0-9\-]+)`")


def load_actual_sets(root: Path) -> tuple[set[str], set[str], set[str]]:
    """(planes, services, worker_event_domains) 실측 집합을 반환."""
    planes_yaml = root / "deploy" / "catalog" / "planes.yaml"
    services_yaml = root / "deploy" / "catalog" / "services.yaml"

    planes: set[str] = set()
    if planes_yaml.exists():
        data = yaml.safe_load(planes_yaml.read_text(encoding="utf-8"))
        planes = set((data.get("planes") or {}).keys())

    services: set[str] = set()
    if services_yaml.exists():
        data = yaml.safe_load(services_yaml.read_text(encoding="utf-8"))
        services = set((data.get("services") or {}).keys())
        services.discard("web")

    worker_domains: set[str] = set()
    worker_main = root / "planes" / "worker_plane" / "plane_worker" / "main.py"
    if worker_main.exists():
        src = worker_main.read_text(encoding="utf-8")
        # _EVENT_DOMAINS 리스트의 첫 번째 튜플 원소(도메인 이름)만 추출.
        block_m = re.search(r"_EVENT_DOMAINS.*?=\s*\[(.*?)\]", src, re.DOTALL)
        if block_m:
            for m in re.finditer(r'\(\s*"([^"]+)"', block_m.group(1)):
                worker_domains.add(m.group(1))

    return planes, services, worker_domains


def audit_documents(doc_paths: list[Path], actual: set[str]) -> int:
    """주어진 문서들에서 백틱 토큰을 추출하여 실측 집합과 비교.

    반환: 문제 검출 0 = 0, 1 이상 = 1.
    """
    orphans_all: list[tuple[Path, str]] = []
    missing_all: list[tuple[Path, set[str]]] = []

    for doc in doc_paths:
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8")
        tokens = set(TOKEN_RE.findall(text))
        # 문서 안에서 언급된 토큰 중 실측 집합에 없는 것 → orphan.
        for t in sorted(tokens):
            # 너무 짧거나 일반 단어 노이즈 완화(3자 이상, 숫자 포함하지 않는 토큰 한정).
            if len(t) < 3:
                continue
            if t.isdigit():
                continue
            # 아주 넓게 "plane 관련 후보" 만 검사하기는 어려우므로,
            # 실측에 있거나 actual 에 없으면 orphan 으로 리포트.
            if t not in actual and "-" in t and t.endswith(("plane", "-adapter")):
                orphans_all.append((doc, t))

        # 실측 집합 원소 중 문서에 아예 언급 없는 것.
        missing = actual - tokens
        if missing:
            missing_all.append((doc, missing))

    for doc, t in orphans_all:
        print(f"[orphan] {doc}: `{t}` (실측에 없음)")
    for doc, missing in missing_all:
        print(f"[missing] {doc}: 언급 누락 {sorted(missing)}")

    issue_count = len(orphans_all) + sum(1 for _ in missing_all if _[1])
    return 0 if issue_count == 0 else 1


def main(argv: list[str] | None = None) -> int:
    """엔트리포인트."""
    parser = argparse.ArgumentParser(description="architecture doc vs actual structure audit (S5)")
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    planes, _services, _worker = load_actual_sets(args.root)
    doc_paths: list[Path] = [args.root / rel for rel in TARGET_DOCS_DEFAULT]
    doc_paths.extend(args.root.glob(ADR_GLOB))

    rc = audit_documents(doc_paths, planes)

    if args.report:
        lines = [
            f"# Architecture Audit — {datetime.now(tz=UTC).date().isoformat()}",
            "",
            f"실측 plane 집합: `{sorted(planes)}`",
            "",
            "## 검출 결과",
            "",
            f"exit code: {rc}",
        ]
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return rc


if __name__ == "__main__":
    sys.exit(main())
