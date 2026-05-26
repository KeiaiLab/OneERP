from __future__ import annotations

from pathlib import Path

import pytest


def test_ADR_0017이_존재하고_핵심_섹션을_포함한다() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    adr = repo_root / "docs" / "governance" / "adr" / "0017-oe-feature-pipeliner-agent-team.md"
    assert adr.is_file(), f"ADR-0017 파일 부재: {adr}"
    text = adr.read_text(encoding="utf-8")
    for section in ("## Context", "## Decision", "## Consequences"):
        assert section in text, f"필수 섹션 누락: {section}"
    assert "oe-feature-pipeliner" in text


def test_ADR_INDEX에_0017이_등재된다() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    index = repo_root / "docs" / "governance" / "adr" / "INDEX.md"
    if not index.is_file():
        pytest.skip("INDEX.md 부재 — 본 환경에서는 검증 생략")
    text = index.read_text(encoding="utf-8")
    assert "0017" in text, "INDEX.md에 0017 미등재"
