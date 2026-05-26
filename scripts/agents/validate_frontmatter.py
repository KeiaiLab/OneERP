"""에이전트 정의 frontmatter 유효성 검증.

Claude Code agent loader가 요구하는 4 필드(name/description/tools/model)와
허용 모델(sonnet/haiku/opus) 화이트리스트를 검사한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml

# 허용 모델: Claude 제품군에서 OneERP가 승인한 3 티어
ALLOWED_MODELS: Final[frozenset[str]] = frozenset({"sonnet", "haiku", "opus"})

# agent loader가 반드시 요구하는 필드 목록 (순서는 문서 관례)
REQUIRED_FIELDS: Final[tuple[str, ...]] = ("name", "description", "tools", "model")


class ValidationError(ValueError):
    """에이전트 frontmatter가 규칙을 위반했을 때 발생한다."""


@dataclass(frozen=True, slots=True)
class AgentFrontmatter:
    """파싱된 frontmatter 값 객체. 불변."""

    name: str
    description: str
    tools: list[str]
    model: str


def parse_frontmatter(md_path: Path) -> AgentFrontmatter:
    """`---` 펜스로 둘러싼 YAML frontmatter를 파싱한다.

    Args:
        md_path: 에이전트 정의 마크다운 파일 경로.

    Returns:
        파싱된 AgentFrontmatter 인스턴스.

    Raises:
        ValidationError: frontmatter 구조가 올바르지 않거나 필수 필드가 누락된 경우.
    """
    text = md_path.read_text(encoding="utf-8")

    # YAML 펜스 시작 검사 — `---\n` 으로 시작해야 함
    if not text.startswith("---\n"):
        raise ValidationError(f"frontmatter 펜스 미시작: {md_path}")

    # `---\n` 기준으로 최대 3 조각으로 분리: ["", yaml_body, body_or_empty]
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        raise ValidationError(f"frontmatter 펜스 미종료: {md_path}")

    fm_yaml = yaml.safe_load(parts[1])
    if not isinstance(fm_yaml, dict):
        raise ValidationError(f"frontmatter가 매핑이 아님: {md_path}")

    # 필수 필드 누락 검사
    missing = [f for f in REQUIRED_FIELDS if f not in fm_yaml]
    if missing:
        raise ValidationError(f"필수 필드 누락 {missing}: {md_path}")

    # tools 값은 쉼표 구분 문자열 또는 YAML 리스트 모두 허용
    # YAML `tools:` (값 없이 키만) → None → TypeError 방지
    tools_raw = fm_yaml["tools"]
    if tools_raw is None:
        raise ValidationError(f"tools 값이 없음: {md_path}")
    if isinstance(tools_raw, str):
        # 빈/whitespace-only 항목 제거
        tools = [t.strip() for t in tools_raw.split(",") if t.strip()]
    else:
        tools = [t for t in list(tools_raw) if str(t).strip()]

    return AgentFrontmatter(
        name=str(fm_yaml["name"]),
        description=str(fm_yaml["description"]),
        tools=tools,
        model=str(fm_yaml["model"]),
    )


def validate(md_path: Path) -> AgentFrontmatter:
    """frontmatter를 파싱하고 비즈니스 규칙을 검증한다.

    Args:
        md_path: 에이전트 정의 마크다운 파일 경로.

    Returns:
        검증을 통과한 AgentFrontmatter 인스턴스.

    Raises:
        ValidationError: 구조 오류 또는 허용되지 않은 model 값인 경우.
    """
    fm = parse_frontmatter(md_path)

    # model 화이트리스트 검사 — 승인되지 않은 모델은 에이전트 실행 거부
    if fm.model not in ALLOWED_MODELS:
        raise ValidationError(
            f"model={fm.model!r} 미허용 (허용: {sorted(ALLOWED_MODELS)}): {md_path}"
        )

    return fm
