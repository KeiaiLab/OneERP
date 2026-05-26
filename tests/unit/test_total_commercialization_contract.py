from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_wave4가_beta_예외가_아니라_23_23_전수통과를_요구한다() -> None:
    adr = (ROOT / "docs/governance/adr/0012-commercialization-wave-mapping.md").read_text(
        encoding="utf-8",
    )
    wave4 = (ROOT / "docs/product/roadmap/engineering/waves/wave-4.md").read_text(
        encoding="utf-8",
    )
    assert "beta 이상 (commercial 강제 X" not in adr
    assert "8 모듈 전부 23/23 기준 통과" in adr
    assert "8 모듈 전부 23/23 기준 통과" in wave4


def test_docs_index가_실재하는_마스터_플랜을_가리킨다() -> None:
    milestones = (ROOT / "docs/product/roadmap/milestones.md").read_text(encoding="utf-8")
    matrix = (ROOT / "docs/product/roadmap/matrix.md").read_text(encoding="utf-8")
    text = (ROOT / "docs/INDEX.md").read_text(encoding="utf-8")
    assert "product/plans/2026-02-09-master-plan.md" not in text
    assert "../.planning/ROADMAP.md" in text
    assert "Wave 4.23/23` (전수 23/23)" in milestones
    assert "Wave 4의 전체 상용 완성은 **8 모듈 전부 23/23 기준 통과**로 판정한다." in matrix
