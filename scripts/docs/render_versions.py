#!/usr/bin/env python3
"""versions.toml → 버전 표 렌더러 (S2).

대상 파일은 `<!-- BEGIN VERSIONS -->` ~ `<!-- END VERSIONS -->` 마커 사이를
파일별 템플릿으로 재생성한다. 마커 바깥의 헤더·문구는 보존된다.

사용:
  python3 scripts/docs/render_versions.py          # dry-run (drift 검사)
  python3 scripts/docs/render_versions.py --write  # 실제 파일 갱신

대상 (유효 파일만 유지):
  - README.md                             (이중언어 3열 표)
  - .claude/CLAUDE.md                     (한국어 3열 표)

spec: docs/superpowers/specs/2026-04-13-docs-health-audit-design.md §3.2
"""

from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[2]
VERSIONS_PATH = ROOT / "versions.toml"

BEGIN = "<!-- BEGIN VERSIONS -->"
END = "<!-- END VERSIONS -->"


def _tech_stack_readme(v: dict[str, str]) -> str:
    """README 이중언어 표. 섹션 제목은 마커 밖에서 유지."""
    return f"""| 영역 (Area) | 기술 (Technology) | 버전 (Version) |
|------|------|------|
| BE 프레임워크 (Framework) | FastAPI + Pydantic v2 | fastapi{v["fastapi"]}, pydantic{v["pydantic"]} |
| BE 린트/포맷 (Lint/Format) | ruff | {v["ruff"]} |
| BE 타입체크 (Type Check) | ty | {v["ty"]} |
| BE 패키지 (Package) | uv workspace | {v["uv"]} |
| FE 프레임워크 (Framework) | Next.js {v["next"]} (App Router, Turbopack) | ^{v["next"]}.0.0 |
| FE 스타일 (Styling) | Tailwind CSS 4 (CSS-first) | ^{v["tailwindcss"]}.0 |
| FE 린트/포맷 (Lint/Format) | Biome | ^{v["biome"]} |
| FE 패키지 (Package) | pnpm workspace | {v["pnpm"]} |
| DB | FerretDB (MongoDB 프로토콜 / MongoDB wire protocol) | {v["ferretdb"]} |
| Python | {v["python"]} | {v["python"]}.x |
| Node.js | {v["node"]} | {v["node"]}.x |

<sub>자동 생성 — 편집하지 마세요. 변경은 `versions.toml` 수정 후 `python3 scripts/docs/render_versions.py --write`.</sub>"""


def _tech_stack_claude(v: dict[str, str]) -> str:
    """CLAUDE.md 한국어 전용 3열 표."""
    return f"""| 영역 | 기술 | 버전 |
|------|------|------|
| BE 프레임워크 | FastAPI + Pydantic v2 | fastapi{v["fastapi"]}, pydantic{v["pydantic"]} |
| BE 린트/포맷 | ruff | {v["ruff"]} |
| BE 타입체크 | ty | {v["ty"]} |
| BE 패키지 | uv workspace | {v["uv"]} |
| FE 프레임워크 | Next.js {v["next"]} (App Router, Turbopack) | ^{v["next"]}.0.0 |
| FE 스타일 | Tailwind CSS 4 (CSS-first) | ^{v["tailwindcss"]}.0 |
| FE 린트/포맷 | Biome | ^{v["biome"]} |
| FE 패키지 | pnpm workspace | {v["pnpm"]} |
| DB | FerretDB (MongoDB 프로토콜) | {v["ferretdb"]} |
| Python | {v["python"]} | {v["python_patch"]} |
| Node.js | {v["node"]} | {v["node"]}.x |

<sub>자동 생성 — `versions.toml` 수정 후 `render_versions.py --write`.</sub>"""


def _prereq_quickstart(v: dict[str, str]) -> str:
    """Quickstart Prerequisite 3열 표."""
    return f"""| 도구 (Tool) | 버전 (Version) | 설치 (Installation) |
|------|------|------|
| macOS | Apple Silicon (M1+) | - |
| Python | {v["python"]}.x | `brew install python@{v["python"]}` |
| Node.js | {v["node"]}.x | `brew install node@{v["node"]}` |
| uv | {v["uv"]} | `brew install astral-sh/tap/uv` |
| pnpm | {v["pnpm"]} | `corepack enable && corepack prepare pnpm@latest --activate` |
| apple/container | 최신 (latest) | [apple/container CLI](https://github.com/apple/container) |

<sub>자동 생성 — `versions.toml` 수정 후 `render_versions.py --write`. `docker-compose.yml`은 PostgreSQL 17 + DocumentDB 확장 + FerretDB {v["ferretdb"]} 조합.</sub>"""


def _toolchain_standards(v: dict[str, str]) -> str:
    """standards.md Python + FE 툴체인 불릿 2블록."""
    return f"""**Python 툴체인 (고정)**

- `uv=={v["uv"]}`
- `ruff=={v["ruff"]}`
- `ty=={v["ty"]}`

**FE 툴체인 (고정)**

- `pnpm=={v["pnpm"]}`
- `biome>={v["biome"]}`
- `next>={v["next"]}.0.0` (App Router + Turbopack)
- `tailwindcss>={v["tailwindcss"]}.0` (CSS-first)

<sub>자동 생성 — `versions.toml` 수정 후 `render_versions.py --write`.</sub>"""


TARGETS: list[tuple[Path, Callable[[dict[str, str]], str]]] = [
    (ROOT / "README.md", _tech_stack_readme),
    (ROOT / ".claude" / "CLAUDE.md", _tech_stack_claude),
]


def _replace_marker_region(text: str, new_body: str) -> tuple[str, bool]:
    """마커 사이 영역을 new_body로 교체. 마커가 없으면 (text, False) 반환."""
    b = text.find(BEGIN)
    e = text.find(END, b + len(BEGIN) if b >= 0 else 0)
    if b == -1 or e == -1:
        return text, False
    before = text[: b + len(BEGIN)]
    after = text[e:]
    rebuilt = f"{before}\n{new_body}\n{after}"
    return rebuilt, True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="실제 파일 갱신")
    args = parser.parse_args(argv)

    if not VERSIONS_PATH.exists():
        print(f"ERROR: {VERSIONS_PATH} 가 없습니다.", file=sys.stderr)
        return 2

    spec = tomllib.loads(VERSIONS_PATH.read_text(encoding="utf-8"))
    versions: dict[str, str] = {k: str(v) for k, v in spec["versions"].items()}

    drift = 0
    missing_marker = 0
    for path, renderer in TARGETS:
        rel = path.relative_to(ROOT)
        if not path.exists():
            print(f"WARNING {rel}: 파일 없음 — skip")
            continue
        current = path.read_text(encoding="utf-8")
        new_body = renderer(versions)
        new_text, ok = _replace_marker_region(current, new_body)
        if not ok:
            print(f"WARN {rel}: 마커(<!-- BEGIN/END VERSIONS -->)가 없습니다.")
            missing_marker += 1
            continue
        if new_text == current:
            print(f"✓ {rel}: 변경 없음")
            continue
        drift += 1
        print(f"△ {rel}: drift 발견")
        if args.write:
            path.write_text(new_text, encoding="utf-8")
            print("  → 갱신 완료")

    print()
    print(f"대상 {len(TARGETS)}개 / drift {drift}개 / 마커 누락 {missing_marker}개")

    if missing_marker > 0 and not args.write:
        print(
            "(마커 누락 파일은 수동으로 <!-- BEGIN VERSIONS --><!-- END VERSIONS --> 쌍을 삽입하세요.)"
        )

    if drift > 0 and not args.write:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
