from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
WORKTREE_ROOT = ROOT / ".worktrees" / "onboarding-master-journey"

_WORKTREE_MISSING = pytest.mark.skipif(
    not WORKTREE_ROOT.exists(),
    reason="onboarding-master-journey 워크트리 없음 — `git worktree add .worktrees/onboarding-master-journey` 실행 필요",
)


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def read_worktree(rel_path: str) -> str:
    return (WORKTREE_ROOT / rel_path).read_text(encoding="utf-8")


@_WORKTREE_MISSING
def test_docs_index_declares_document_roles() -> None:
    text = read_worktree("docs/INDEX.md")

    assert "## 문서 역할 규칙" in text
    assert "정본" in text
    assert "보관" in text


@_WORKTREE_MISSING
def test_user_facing_docs_are_top_level_canonical() -> None:
    index = read_worktree("docs/INDEX.md")
    tutorials = read_worktree("docs/tutorials/INDEX.md")
    user_manual = read_worktree("docs/user-manual/INDEX.md")
    guide = read_worktree("docs/product/scope/MASTER-DOC-GUIDE.md")

    assert "사용자-facing 최상위 정본" in index
    assert "tutorials/" in index
    assert "tutorials/INDEX.md" in index
    assert "사용자-facing 최상위 정본 축" in tutorials
    assert "docs/tutorials/*.md" in tutorials
    assert "user-manual/" in index
    assert "내부 근거 문서" in index
    assert "사용자-facing 최상위 정본" in user_manual
    assert "구조/레이어/구현 관례 내부 기준" in guide


def test_legacy_amaranth_gap_doc_is_marked_archived() -> None:
    text = read("docs/gap-analysis-amaranth10.md")

    assert "보관 문서" in text
    assert "docs/product/scope/08-amaranth10-gap-analysis.md" in text
    assert "docs/product/COMPETITIVE-GAP-ANALYSIS.md" in text


@_WORKTREE_MISSING
def test_onboarding_docs_share_minimum_structure() -> None:
    required_headings = (
        "## 사전 조건 (Prerequisites)",
        "## 완료 조건 (Completion Criteria)",
        "## 다음 단계 (Next Step)",
    )

    module_template = read_worktree("docs/product/onboarding/module-template.md")
    assert "## 사전 조건 (Prerequisites)" in module_template
    assert "## 완료 조건 (Completion Criteria)" in module_template
    assert "## 다음 단계 (Next Step)" in module_template

    for folder in ("docs/tutorials", "docs/user-manual"):
        for path in sorted((WORKTREE_ROOT / folder).glob("*.md")):
            if path.name == "INDEX.md":
                continue
            text = path.read_text(encoding="utf-8")
            assert all(heading in text for heading in required_headings), path
