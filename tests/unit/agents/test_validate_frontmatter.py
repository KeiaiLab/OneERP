from __future__ import annotations

from pathlib import Path

import pytest

from scripts.agents.validate_frontmatter import (
    AgentFrontmatter,
    ValidationError,
    parse_frontmatter,
    validate,
)


def test_유효한_frontmatter는_AgentFrontmatter를_반환한다(tmp_path: Path) -> None:
    md = tmp_path / "agent.md"
    md.write_text(
        "---\n"
        "name: oe-test\n"
        "description: 테스트 에이전트\n"
        "tools: Read, Write\n"
        "model: sonnet\n"
        "---\n"
        "본문\n",
        encoding="utf-8",
    )
    fm: AgentFrontmatter = parse_frontmatter(md)
    assert fm.name == "oe-test"
    assert fm.tools == ["Read", "Write"]
    assert fm.model == "sonnet"


def test_name_필드_누락시_ValidationError(tmp_path: Path) -> None:
    md = tmp_path / "agent.md"
    md.write_text(
        "---\ndescription: 누락 테스트\ntools: Read\nmodel: sonnet\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="name"):
        validate(md)


def test_허용되지_않은_model은_ValidationError(tmp_path: Path) -> None:
    md = tmp_path / "agent.md"
    md.write_text(
        "---\nname: oe-bad\ndescription: 잘못된 모델\ntools: Read\nmodel: gpt-4\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="model"):
        validate(md)


def test_tools_None은_ValidationError(tmp_path: Path) -> None:
    """YAML `tools:` (값 없이 키만 존재) → None → ValidationError."""
    md = tmp_path / "agent.md"
    md.write_text(
        "---\nname: oe-none\ndescription: tools None 테스트\ntools:\nmodel: sonnet\n---\n",
        encoding="utf-8",
    )
    with pytest.raises(ValidationError, match="tools"):
        parse_frontmatter(md)


def test_tools_YAML_리스트도_정상_파싱(tmp_path: Path) -> None:
    """YAML 리스트 형식 `tools: [Read, Write]` → fm.tools == ['Read', 'Write']."""
    md = tmp_path / "agent.md"
    md.write_text(
        "---\nname: oe-list\ndescription: YAML 리스트 테스트\ntools: [Read, Write]\nmodel: sonnet\n---\n본문\n",
        encoding="utf-8",
    )
    fm: AgentFrontmatter = parse_frontmatter(md)
    assert fm.tools == ["Read", "Write"]


def test_oe_feature_pipeliner_정의가_유효하다() -> None:
    """프로젝트의 실제 oe-feature-pipeliner.md를 검증한다."""
    repo_root = Path(__file__).resolve().parents[3]
    md = repo_root / ".claude" / "agents" / "oe-feature-pipeliner.md"
    fm = validate(md)
    assert fm.name == "oe-feature-pipeliner"
    assert fm.model == "sonnet"
    assert "Read" in fm.tools
    assert "Bash" in fm.tools
