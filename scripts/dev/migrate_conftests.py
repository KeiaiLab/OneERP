#!/usr/bin/env python3
"""services/*/*/tests/unit/conftest.py 48개 일괄 마이그레이션.

이전 패턴(서비스별 25~40줄 sys.path 조작 + mock 설정 복붙) →
`oneerp_core.testing.make_service_test_client` 팩토리 기반 표준 템플릿.

서비스별 특화 fixture(예: selling 의 quotations_mod) 는 AST 로 추출해
표준 템플릿 말미에 보존한다.

사용:
  python3 scripts/dev/migrate_conftests.py           # dry-run (변경 없음)
  python3 scripts/dev/migrate_conftests.py --write   # 실제 적용
"""

from __future__ import annotations

import argparse
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICES = ROOT / "services"

STANDARD_FIXTURES = {"mock_collection", "test_client", "_clear_settings_cache"}

TEMPLATE = '''"""{service_name} 단위 테스트 공통 fixture.

M1 공통화 — `oneerp_core.testing` 팩토리 기반.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from oneerp_core.testing import (
    clear_settings_cache,
    make_service_test_client,
    mock_repository_collection,
)

os.environ.setdefault("ONEERP_DEBUG", "true")

_SERVICE_ROOT = Path(__file__).resolve().parents[2]
_client = make_service_test_client(_SERVICE_ROOT)


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    clear_settings_cache()


@pytest.fixture
def mock_collection():
    with mock_repository_collection() as mc:
        yield mc


@pytest.fixture
def test_client():
    return _client
'''


def _extract_custom_fixtures(original: str) -> list[str]:
    """표준 이름(STANDARD_FIXTURES) 이외의 @pytest.fixture 정의 소스 블록 추출.

    들여쓰기 유실 방지를 위해 소스 라인 슬라이스 사용.
    """
    try:
        tree = ast.parse(original)
    except SyntaxError:
        return []

    lines = original.splitlines(keepends=True)
    blocks: list[str] = []

    for node in tree.body:
        if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        if node.name in STANDARD_FIXTURES:
            continue
        # @pytest.fixture 데코레이터가 있는 함수만 추출
        is_fixture = False
        for dec in node.decorator_list:
            src = ast.unparse(dec)
            if "pytest.fixture" in src or src.startswith("fixture"):
                is_fixture = True
                break
        if not is_fixture:
            continue

        # 데코레이터 중 가장 위 줄번호 찾기
        start_line = node.lineno
        for dec in node.decorator_list:
            if dec.lineno < start_line:
                start_line = dec.lineno
        end_line = getattr(node, "end_lineno", node.lineno)
        snippet = "".join(lines[start_line - 1 : end_line])
        blocks.append(snippet.rstrip() + "\n")
    return blocks


def _migrate_one(path: Path, *, write: bool) -> tuple[bool, int, int]:
    original = path.read_text(encoding="utf-8")
    service_name = path.parents[2].name

    custom_blocks = _extract_custom_fixtures(original)
    extra = ""
    if custom_blocks:
        extra = "\n\n" + "\n\n".join(custom_blocks).rstrip() + "\n"

    new_content = TEMPLATE.format(service_name=service_name) + extra

    old_lines = len(original.splitlines())
    new_lines = len(new_content.splitlines())

    if new_content == original:
        return False, old_lines, new_lines

    if write:
        path.write_text(new_content, encoding="utf-8")
    return True, old_lines, new_lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true", help="실제 파일 수정")
    parser.add_argument("--limit", type=int, default=0, help="처리 개수 제한 (0=전체)")
    args = parser.parse_args()

    conftests = sorted(SERVICES.glob("*/*/tests/unit/conftest.py"))
    if args.limit > 0:
        conftests = conftests[: args.limit]

    total_old = 0
    total_new = 0
    changed = 0

    for path in conftests:
        did_change, old_lines, new_lines = _migrate_one(path, write=args.write)
        total_old += old_lines
        total_new += new_lines
        if did_change:
            changed += 1
            marker = "→ 갱신" if args.write else "drift"
            print(f"△ {path.relative_to(ROOT)}: {old_lines}→{new_lines} 줄 ({marker})")

    print()
    print(
        f"대상 {len(conftests)}개 / 변경 {changed}개 / "
        f"LOC {total_old} → {total_new} (감축 {total_old - total_new})"
    )

    if changed > 0 and not args.write:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
