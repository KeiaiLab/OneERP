from __future__ import annotations

from pathlib import Path


def test_AGENTS_md가_pipeliner와_매트릭스_위치를_명시한다() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    agents = repo_root / "AGENTS.md"
    text = agents.read_text(encoding="utf-8")
    # 매트릭스 + pipeliner 핵심 키워드
    assert "oe-feature-pipeliner" in text
    assert "_routing-matrix.md" in text
    # 라인업 단락 핵심 항목
    assert "에이전트 라인업" in text
    assert "ce-planner" in text
    assert "scripts/agents/" in text
    assert "ADR-0017" in text
