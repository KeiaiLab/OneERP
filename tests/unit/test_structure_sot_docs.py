from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _read(relative_path: str) -> str:
    path = ROOT / relative_path
    assert path.exists(), f"문서가 없습니다: {path}"
    return path.read_text(encoding="utf-8")


def test_structure_sot_docs_use_current_repo_paths() -> None:
    expectations = {
        "docs/infra/inventory/repo.md": {
            "contains": ["core/oneerp_core/", "web/"],
            "not_contains": ["packages/core/", "apps/web/"],
        },
        "docs/infra/inventory/00-checklist.md": {
            "contains": ["core/oneerp_core/"],
            "not_contains": ["packages/core/oneerp_core/"],
        },
        "docs/onboarding/01-architecture-overview.md": {
            "contains": ["core/oneerp_core/"],
            "not_contains": ["packages/core/"],
        },
        "web/README.md": {
            "contains": ["web/"],
            "not_contains": ["apps/web/"],
        },
    }

    for relative_path, rules in expectations.items():
        text = _read(relative_path)
        for expected in rules["contains"]:
            assert expected in text, f"{relative_path}에 현재 경로 기준 `{expected}`가 없습니다"
        for legacy in rules["not_contains"]:
            assert legacy not in text, f"{relative_path}에 구형 경로 `{legacy}`가 남아 있습니다"
