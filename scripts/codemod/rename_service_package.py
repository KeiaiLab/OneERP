"""서비스 패키지 리네임 코드모드 — ADR-0014 M1.5.

`services/{domain}/{service}/app/` → `services/{domain}/{service}/oneerp_{service}_app/`
패턴으로 서비스 패키지를 리네임한다. sys.modules["app"] 단일 점유로 인한
plane 다중 마운트 제약(제약 A)을 해결한다.

수행 작업:
    1. 디렉토리 이동: `app/` → `oneerp_{service}_app/`
    2. pyproject.toml: `packages = ["app"]` → `packages = ["oneerp_{service}_app"]`
    3. Dockerfile: CMD `app.main:app` → `oneerp_{service}_app.main:app`
    4. 서비스 내부 `from app.X import` / `import app.X` 절대 import 리라이트
    5. 테스트에서 `from app.X import` 리라이트 (단, conftest의
       register_service_path/load_service_app 호출은 유지 — 헬퍼가
       package_name 인자로 해석)

사용:
    uv run python scripts/codemod/rename_service_package.py <service_root>
    예) uv run python scripts/codemod/rename_service_package.py services/sales/selling
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def rename_service(service_root: Path) -> None:
    """단일 서비스를 리네임한다.

    Args:
        service_root: 서비스 루트 (예: services/sales/selling).

    Raises:
        FileNotFoundError: app 디렉토리가 없을 때.
        RuntimeError: 이미 리네임된 서비스일 때.
    """
    service_root = service_root.resolve()
    if not service_root.is_dir():
        raise FileNotFoundError(f"서비스 루트가 없다: {service_root}")

    service_name = service_root.name  # e.g. "selling"
    new_pkg = f"oneerp_{service_name}_app"  # Python 식별자 규칙: -  → _
    new_pkg = new_pkg.replace("-", "_")

    old_dir = service_root / "app"
    new_dir = service_root / new_pkg

    if new_dir.is_dir():
        raise RuntimeError(f"{service_root.name}: 이미 리네임됨 ({new_pkg}/ 존재)")
    if not old_dir.is_dir():
        raise FileNotFoundError(f"{service_root.name}: app/ 디렉토리 없음")

    # 1) 디렉토리 이동
    old_dir.rename(new_dir)

    # 2) pyproject.toml
    pyproject = service_root / "pyproject.toml"
    if pyproject.is_file():
        txt = pyproject.read_text(encoding="utf-8")
        txt = txt.replace('packages = ["app"]', f'packages = ["{new_pkg}"]')
        pyproject.write_text(txt, encoding="utf-8")

    # 3) Dockerfile CMD
    dockerfile = service_root / "Dockerfile"
    if dockerfile.is_file():
        txt = dockerfile.read_text(encoding="utf-8")
        txt = txt.replace('"app.main:app"', f'"{new_pkg}.main:app"')
        dockerfile.write_text(txt, encoding="utf-8")

    # 4) 절대 import 리라이트 (서비스 내부 + tests)
    _rewrite_absolute_imports(service_root, new_pkg)


_IMPORT_PATTERNS = [
    # 들여쓰기 포함 — 함수/메서드 내부 지연 import 도 커버
    (re.compile(r"(?m)^(\s*)from app\.(.+) import"), r"\1from {pkg}.\2 import"),
    (re.compile(r"(?m)^(\s*)from app import"), r"\1from {pkg} import"),
    (re.compile(r"(?m)^(\s*)import app\.(.+)$"), r"\1import {pkg}.\2"),
    (re.compile(r"(?m)^(\s*)import app$"), r"\1import {pkg}"),
    # 문자열 기반 참조: @patch("app.X"), importlib.import_module("app.X") 등
    (re.compile(r'"app\.'), r'"{pkg}.'),
    (re.compile(r"'app\."), r"'{pkg}."),
]


def _rewrite_absolute_imports(service_root: Path, new_pkg: str) -> None:
    """서비스 루트 아래 모든 .py에서 `app.X` 절대 import를 리라이트."""
    for py in service_root.rglob("*.py"):
        txt = py.read_text(encoding="utf-8")
        new = txt
        for pat, repl_tmpl in _IMPORT_PATTERNS:
            new = pat.sub(repl_tmpl.format(pkg=new_pkg), new)
        if new != txt:
            py.write_text(new, encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: rename_service_package.py <service_root>", file=sys.stderr)
        return 2
    try:
        rename_service(Path(argv[1]))
    except (FileNotFoundError, RuntimeError) as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print(f"OK renamed: {argv[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
