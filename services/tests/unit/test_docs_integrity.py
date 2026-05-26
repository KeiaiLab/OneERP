from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "docs" / "check_integrity.py"


def load_module():
    if not SCRIPT_PATH.exists():
        pytest.fail(f"문서 무결성 검사 스크립트가 없습니다: {SCRIPT_PATH}")

    spec = importlib.util.spec_from_file_location("check_integrity", SCRIPT_PATH)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


WORKTREE_ROOT = ROOT / ".worktrees" / "onboarding-master-journey"


def read_worktree_doc(relative_path: str) -> str:
    path = WORKTREE_ROOT / relative_path
    assert path.exists(), f"문서가 없습니다: {path}"
    return path.read_text(encoding="utf-8")


def assert_required_sections(text: str, *, path: str) -> None:
    for heading in ("## 사전 조건", "## 완료 조건", "## 다음 단계"):
        assert heading in text, f"{path}에 {heading} 섹션이 없습니다"
    assert re.search(r"## 다음 단계[\s\S]*\[[^\]]+\]\([^)]+\)", text), (
        f"{path}의 다음 단계 섹션에 링크가 없습니다"
    )


def test_onboarding_journey_assets_exist_and_cover_phases() -> None:
    journey_map = read_worktree_doc("docs/product/onboarding/journey-map.md")
    step_catalog = read_worktree_doc("docs/product/onboarding/step-catalog.yaml")

    for phrase in (
        "초기 구축",
        "CL1",
        "CL5",
        "모듈 확장",
    ):
        assert phrase in journey_map, f"journey-map에 {phrase}가 없습니다"

    for phrase in (
        "initial_build",
        "cl1",
        "cl5",
        "module_expansion",
    ):
        assert phrase in step_catalog, f"step-catalog에 {phrase}가 없습니다"


def test_cl1_and_cl5_are_marked_as_core_deep_journeys_and_linked() -> None:
    journey_map = read_worktree_doc("docs/product/onboarding/journey-map.md")
    step_catalog = read_worktree_doc("docs/product/onboarding/step-catalog.yaml")
    accounting = read_worktree_doc("docs/user-manual/01-accounting.md")
    expenses = read_worktree_doc("docs/user-manual/07-expenses.md")
    approval = read_worktree_doc("docs/user-manual/13-approval.md")
    o2c = read_worktree_doc("docs/tutorials/01-order-to-cash.md")
    p2p = read_worktree_doc("docs/tutorials/02-procure-to-pay.md")
    expense = read_worktree_doc("docs/tutorials/03-expense-approval.md")

    assert "핵심 심화 여정" in journey_map
    assert "핵심 심화 여정" in step_catalog
    assert "[판매→수금 튜토리얼](../tutorials/01-order-to-cash.md)" in accounting
    assert "[구매→지급 튜토리얼](../tutorials/02-procure-to-pay.md)" in accounting
    assert "[회계 모듈](../user-manual/01-accounting.md)" in o2c
    assert "[회계 모듈](../user-manual/01-accounting.md)" in p2p
    assert "[경비 모듈](../user-manual/07-expenses.md)" in expense
    assert "[전자결재 모듈](../user-manual/13-approval.md)" in expense
    assert "[경비→결재→회계 튜토리얼](../tutorials/03-expense-approval.md)" in expenses
    assert "[경비→결재→회계 튜토리얼](../tutorials/03-expense-approval.md)" in approval


@pytest.mark.parametrize(
    ("relative_path", "expected_heading"),
    [
        ("docs/tutorials/01-order-to-cash.md", "# 튜토리얼: Order-to-Cash"),
        ("docs/tutorials/02-procure-to-pay.md", "# 튜토리얼: Procure-to-Pay"),
        ("docs/tutorials/03-expense-approval.md", "# 튜토리얼: Expense-Approval"),
        ("docs/tutorials/10-admin-setup.md", "# 튜토리얼: Initial Setup"),
        ("docs/user-manual/00-getting-started.md", "# 시작하기"),
        ("docs/user-manual/01-accounting.md", "# 회계 모듈"),
        ("docs/user-manual/07-expenses.md", "# 경비 모듈"),
        ("docs/user-manual/13-approval.md", "# 전자결재 모듈"),
        ("docs/user-manual/14-admin.md", "# 관리자 모듈"),
    ],
)
def test_representative_docs_include_required_onboarding_sections(
    relative_path: str, expected_heading: str
) -> None:
    text = read_worktree_doc(relative_path)
    assert expected_heading in text
    assert_required_sections(text, path=relative_path)


def test_fenced_code_links_are_ignored(tmp_path: Path) -> None:
    module = load_module()

    docs_root = tmp_path / "docs"
    write(docs_root / "INDEX.md", "# index\n")
    write(
        docs_root / "guide.md",
        """# 가이드

```markdown
[깨진 예시](missing.md)
```
""",
    )

    report = module.build_integrity_report(tmp_path, seed="docs/INDEX.md")

    assert report.broken_links == []


def test_detects_broken_local_links(tmp_path: Path) -> None:
    module = load_module()

    docs_root = tmp_path / "docs"
    write(docs_root / "INDEX.md", "# index\n- [가이드](guide.md)\n")
    write(docs_root / "guide.md", "# guide\n- [없는 문서](missing.md)\n")

    report = module.build_integrity_report(tmp_path, seed="docs/INDEX.md")

    assert [(item.source, item.target) for item in report.broken_links] == [
        ("docs/guide.md", "missing.md")
    ]


def test_inline_code_links_are_ignored(tmp_path: Path) -> None:
    module = load_module()

    docs_root = tmp_path / "docs"
    write(docs_root / "INDEX.md", "# index\n")
    write(
        docs_root / "guide.md",
        "# guide\n`예시 링크 [없는 문서](missing.md)`\n",
    )

    report = module.build_integrity_report(tmp_path, seed="docs/INDEX.md")

    assert report.broken_links == []


def test_detects_unreachable_docs_from_index(tmp_path: Path) -> None:
    module = load_module()

    docs_root = tmp_path / "docs"
    write(docs_root / "INDEX.md", "# index\n- [가이드](guide.md)\n")
    write(docs_root / "guide.md", "# guide\n")
    write(docs_root / "orphan.md", "# orphan\n")

    report = module.build_integrity_report(tmp_path, seed="docs/INDEX.md")

    assert report.unreachable_docs == ["docs/orphan.md"]


def test_worktrees_are_ignored(tmp_path: Path) -> None:
    module = load_module()

    docs_root = tmp_path / "docs"
    write(docs_root / "INDEX.md", "# index\n")
    write(
        tmp_path / ".worktrees" / "feature-a" / "docs" / "broken.md",
        "# broken\n- [없는 문서](missing.md)\n",
    )

    report = module.build_integrity_report(tmp_path, seed="docs/INDEX.md")

    assert report.broken_links == []
    assert report.unreachable_docs == []
