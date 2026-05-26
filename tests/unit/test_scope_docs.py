from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCOPE_ROOT = ROOT / "docs" / "product" / "scope"
ARCHITECTURE_MAP = ROOT / "docs" / "ARCHITECTURE-MAP.md"


def test_scope_docs_entrypoints_exist_and_are_mapped() -> None:
    scope_readme = SCOPE_ROOT / "README.md"
    modules_readme = SCOPE_ROOT / "modules" / "README.md"

    assert scope_readme.exists(), "docs/product/scope/README.md 가 없습니다"
    assert modules_readme.exists(), "docs/product/scope/modules/README.md 가 없습니다"

    architecture_map = ARCHITECTURE_MAP.read_text(encoding="utf-8")
    assert "docs/product/scope/README.md" in architecture_map
    assert "docs/product/scope/modules/README.md" in architecture_map
