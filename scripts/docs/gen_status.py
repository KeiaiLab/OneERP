#!/usr/bin/env python3
"""docs/STATUS.md frontmatter 자동 갱신기.

OneERP 이개적 SoT 파일의 frontmatter를 실측값으로 동기화한다:
  - last_updated (오늘 날짜, ISO 8601)
  - last_commit  (git rev-parse --short HEAD)
  - last_pr      (git log에서 추출한 가장 최근 "Merge pull request #N")
  - service_count (services/{domain}/{svc} 개수)
  - module_count  (docs/product/scope/modules/ 하위 디렉토리 개수)

사용:
  python3 scripts/docs/gen_status.py            # dry-run (차이만 보고, 종료코드 1 if drift)
  python3 scripts/docs/gen_status.py --write    # 실제 적용

CI 연동:
  docs-status-fresh job에서 dry-run 실행 후 last_updated이 7일 초과면 fail.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

STATUS_PATH = Path("docs/STATUS.md")
ROOT = Path(__file__).resolve().parents[2]


def _run(cmd: list[str]) -> str:
    """서브프로세스 실행 + stdout 반환 (실패 시 빈 문자열)."""
    try:
        out = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=True).stdout
        return out.strip()
    except subprocess.CalledProcessError:
        return ""


def _last_commit() -> str:
    return _run(["git", "rev-parse", "--short", "HEAD"]) or "unknown"


def _last_pr() -> str:
    log = _run(["git", "log", "--oneline", "-200"])
    for line in log.splitlines():
        m = re.search(r"Merge pull request #(\d+)", line)
        if m:
            return m.group(1)
    return "?"


def _service_count() -> int:
    services_dir = ROOT / "services"
    if not services_dir.is_dir():
        return 0
    count = 0
    for domain in services_dir.iterdir():
        if not domain.is_dir():
            continue
        for svc in domain.iterdir():
            if svc.is_dir() and (svc / "pyproject.toml").exists():
                count += 1
    return count


def _module_count() -> int:
    modules_dir = ROOT / "docs" / "product" / "scope" / "modules"
    if not modules_dir.is_dir():
        return 0
    return sum(1 for p in modules_dir.iterdir() if p.is_dir())


def _current_frontmatter(text: str) -> tuple[str, str, str]:
    """파일 본문을 (frontmatter, 본문, 구분자 이후 개행) 으로 분해."""
    if not text.startswith("---\n"):
        raise SystemExit("docs/STATUS.md: frontmatter(---)가 없습니다.")
    end = text.find("\n---\n", 4)
    if end == -1:
        raise SystemExit("docs/STATUS.md: frontmatter 종료(---)를 찾지 못했습니다.")
    return text[4:end], text[end + 5 :], "\n"


def _rewrite_field(fm: str, key: str, value: str | int) -> str:
    """frontmatter 텍스트에서 단일 key를 최상위 레벨에서만 치환."""
    pattern = re.compile(rf"^{re.escape(key)}:.*$", re.MULTILINE)
    replacement = f"{key}: {value}"
    if pattern.search(fm):
        return pattern.sub(replacement, fm, count=1)
    return fm + f"\n{replacement}"


def main() -> int:
    parser = argparse.ArgumentParser(description="docs/STATUS.md frontmatter 갱신")
    parser.add_argument("--write", action="store_true", help="변경 사항을 실제 저장")
    args = parser.parse_args()

    path = ROOT / STATUS_PATH
    if not path.exists():
        print(f"ERROR: {STATUS_PATH} 가 없습니다.", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8")
    fm, body, _ = _current_frontmatter(text)

    targets = {
        "last_updated": datetime.now(UTC).date().isoformat(),
        "last_commit": _last_commit(),
        "last_pr": _last_pr(),
        "service_count": _service_count(),
        "module_count": _module_count(),
    }

    new_fm = fm
    diffs: list[tuple[str, str, str]] = []
    for key, new_val in targets.items():
        current = re.search(rf"^{re.escape(key)}:\s*(.*)$", fm, re.MULTILINE)
        current_val = current.group(1).strip() if current else "(없음)"
        if str(current_val) != str(new_val):
            diffs.append((key, current_val, str(new_val)))
            new_fm = _rewrite_field(new_fm, key, new_val)

    if not diffs:
        print("✓ docs/STATUS.md frontmatter는 최신 상태입니다.")
        return 0

    print("변경 후보:")
    for key, old, new in diffs:
        print(f"  {key}: {old}  →  {new}")

    if args.write:
        path.write_text(f"---\n{new_fm}\n---\n{body}", encoding="utf-8")
        print(f"\n적용 완료: {STATUS_PATH}")
        return 0

    print("\n(dry-run, --write 로 실제 적용)")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
