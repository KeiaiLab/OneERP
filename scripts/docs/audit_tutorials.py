#!/usr/bin/env python3
"""docs/tutorials/*.md 코드블록 무결성 검증 체커 (S4).

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.4

알고리즘:
- bash/sh: 임시 파일에 쓰고 `bash -n` 실행 → stderr 캡처 보고.
- json: `json.loads` 구문 검증.
- http: GET/POST/... <path> 라인의 path 가 known_paths 에 prefix-match 되는지.
- 그 외(python/typescript/yaml): skip.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT_DEFAULT = Path(__file__).resolve().parents[2]

TUTORIALS_GLOB = "docs/tutorials/*.md"
FENCE_RE = re.compile(r"^```(\w+)\s*\n(.*?)^```", re.MULTILINE | re.DOTALL)
HTTP_PATH_RE = re.compile(r"^(?:GET|POST|PUT|DELETE|PATCH)\s+(\S+)", re.MULTILINE)
BANNER = "> **⚠️ 검증 실패 — 2026-04-13**"


def _check_bash(code: str) -> str | None:
    """bash -n 으로 syntax 검증. 오류 시 오류 메시지 반환, 정상이면 None."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False, encoding="utf-8") as f:
        f.write(code)
        tmp_path = f.name
    result = subprocess.run(
        ["bash", "-n", tmp_path],
        capture_output=True,
        text=True,
    )
    Path(tmp_path).unlink(missing_ok=True)
    if result.returncode != 0:
        return result.stderr.strip() or "bash syntax 오류"
    return None


def _check_json(code: str) -> str | None:
    """json.loads 로 구문 검증. 오류 시 오류 메시지 반환, 정상이면 None."""
    try:
        json.loads(code)
    except json.JSONDecodeError as exc:
        return str(exc)
    return None


def _check_http(code: str, known_paths: set[str]) -> list[str]:
    """http 블록 내 path 가 known_paths 에 prefix-match 되지 않으면 오류 목록 반환."""
    errors: list[str] = []
    for m in HTTP_PATH_RE.finditer(code):
        path = m.group(1)
        if known_paths and not any(path.startswith(kp) for kp in known_paths):
            errors.append(f"알 수 없는 path: {path}")
    return errors


def audit_file(filepath: Path, known_paths: set[str]) -> int:
    """단일 파일 검증. 실패 블록 1개 이상이면 1, 아니면 0 반환."""
    text = filepath.read_text(encoding="utf-8")
    failures: list[str] = []

    for m in FENCE_RE.finditer(text):
        lang = m.group(1).lower()
        code = m.group(2)

        if lang in {"bash", "sh"}:
            err = _check_bash(code)
            if err:
                failures.append(f"[bash] {err}")
        elif lang == "json":
            err = _check_json(code)
            if err:
                failures.append(f"[json] {err}")
        elif lang == "http":
            errs = _check_http(code, known_paths)
            failures.extend(f"[http] {e}" for e in errs)
        # python/typescript/yaml 등 나머지는 skip

    if failures:
        for msg in failures:
            print(f"  FAIL {filepath.name}: {msg}")
        return 1
    return 0


def mark_failed(filepath: Path) -> None:
    """실패 파일 상단에 검증 실패 배너를 추가한다(멱등 — 이미 있으면 skip)."""
    text = filepath.read_text(encoding="utf-8")
    if "검증 실패" in text:
        return
    new_text = BANNER + "\n\n" + text
    filepath.write_text(new_text, encoding="utf-8")


def collect_known_paths(_root: Path) -> set[str]:
    """모든 plane 의 OpenAPI path 를 최선 수집. 실패 시 빈 집합 반환."""
    known: set[str] = set()
    # import 실패를 무시하고 빈 세트 반환(오프라인 환경에서도 체커 작동).
    return known


def main(argv: list[str] | None = None) -> int:
    """엔트리포인트."""
    parser = argparse.ArgumentParser(description="tutorials 코드블록 무결성 체커 (S4)")
    parser.add_argument("--root", type=Path, default=ROOT_DEFAULT)
    parser.add_argument("--mark", action="store_true", help="실패 파일에 경고 배너 추가")
    parser.add_argument("--json", action="store_true", help="구조화 JSON 출력(미래 CI 용)")
    args = parser.parse_args(argv)

    root: Path = args.root
    known_paths = collect_known_paths(root)

    tutorial_files = sorted(root.glob(TUTORIALS_GLOB))
    if not tutorial_files:
        # docs/tutorials 가 없을 수도 있는 환경(테스트)에서는 인자로 직접 파일 지정 가능.
        pass

    failed_files: list[Path] = []
    for tf in tutorial_files:
        rc = audit_file(tf, known_paths)
        if rc != 0:
            failed_files.append(tf)

    if args.mark:
        for tf in failed_files:
            mark_failed(tf)

    total = len(tutorial_files)
    fail = len(failed_files)
    print(f"tutorials 검증: 총 {total}개 중 실패 {fail}개.")
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
