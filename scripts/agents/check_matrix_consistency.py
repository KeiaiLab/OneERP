"""라우팅 매트릭스 정합성 검증.

매트릭스 표가 참조하는 모든 에이전트 이름이 프로젝트 또는 글로벌 디렉토리에
실존하는지 검사한다. dash(`—`)와 화이트리스트(plugin:* 등)는 통과.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

DASH: Final[frozenset[str]] = frozenset({"—", "-", ""})
PLUGIN_ALLOWLIST_PREFIXES: Final[tuple[str, ...]] = ("feature-dev:", "code-review:")


class MatrixError(ValueError):
    """라우팅 매트릭스가 정합성 룰을 위반했을 때."""


@dataclass(frozen=True, slots=True)
class MatrixRow:
    work_type: str
    caller: str
    primary: str
    secondary: str
    skip: str


def parse_matrix_table(md_path: Path) -> list[MatrixRow]:
    """`## 표` 다음의 markdown 표를 파싱한다.

    I-1+I-3: `^## 표$` 앵커로 `## 표 분류` / `### 표` 등 부분 매치 차단.
    I-2: 마지막 행 `\\n` 없는 EOF도 정상 파싱.
    I-4: 5셀 미만 행은 silent skip 대신 MatrixError.
    """
    text = md_path.read_text(encoding="utf-8")

    # I-1+I-3: 정확히 `## 표`만 매치 (h2, 행 내 다른 텍스트 없음)
    header_match = re.search(r"^## 표\s*$", text, re.MULTILINE)
    if not header_match:
        raise MatrixError(f"`## 표` 섹션을 찾지 못함: {md_path}")

    # I-2: 헤딩 이후 텍스트에서 표 추출, 마지막 `\n` optional
    remaining = text[header_match.end() :].lstrip()
    table_match = re.match(r"((?:\|[^\n]+\|\n?)+)", remaining)
    if not table_match:
        raise MatrixError(f"`## 표` 다음에 markdown 표가 없음: {md_path}")

    raw_lines = [ln for ln in table_match.group(1).splitlines() if ln.startswith("|")]
    if len(raw_lines) < 3:
        raise MatrixError(f"표 행 부족(헤더+구분자+1행): {md_path}")

    rows: list[MatrixRow] = []
    for idx, ln in enumerate(raw_lines[2:], start=3):  # 1-indexed (헤더=1, 구분자=2)
        cells = [c.strip() for c in ln.strip("|").split("|")]
        # I-4: silent skip 대신 MatrixError
        if len(cells) < 5:
            raise MatrixError(f"행 #{idx}의 컬럼 수 부족(필요 ≥5, 실제 {len(cells)}): {ln!r}")
        rows.append(
            MatrixRow(
                work_type=cells[0],
                caller=cells[1],
                primary=cells[2],
                secondary=cells[3],
                skip=cells[4],
            )
        )

    # I-4: 데이터 행 0건도 오류
    if not rows:
        raise MatrixError(f"표에 데이터 행이 없음: {md_path}")

    return rows


def _agent_exists(name: str, project_agents: Path, global_agents: Path) -> bool:
    if name in DASH:
        return True
    if any(name.startswith(p) for p in PLUGIN_ALLOWLIST_PREFIXES):
        return True
    # 가정: 첫 단일 `<prefix>-` 세그먼트 기준. multi-hyphen 이름(예: `code-quality-gate`)의
    # 슬래시 묶음 표기는 사용 금지 (이 패턴은 ce-*/oe-* 같은 단일 prefix만 지원).
    # multi-agent 표기 지원 (예: "ce-artisan/scribe/executor"는 ce 접두 묶음)
    # 슬래시로 분리된 모든 토큰이 실존하면 True. 첫 토큰이 fully-qualified 이름,
    # 나머지는 첫 토큰의 접두를 공유하는 짧은 이름.
    if "/" in name:
        tokens = [t.strip() for t in name.split("/") if t.strip()]
        if not tokens:
            return False
        first = tokens[0]
        # first는 fully-qualified (예: "ce-artisan")
        if not _single_agent_exists(first, project_agents, global_agents):
            return False
        # first의 접두 추출 (예: "ce-artisan" → "ce-")
        prefix_match = re.match(r"^([a-z]+-)", first)
        if not prefix_match:
            return False
        prefix = prefix_match.group(1)
        # 나머지 토큰은 prefix + token 형태로 검증 (예: "scribe" → "ce-scribe")
        for tok in tokens[1:]:
            full_name = prefix + tok
            if not _single_agent_exists(full_name, project_agents, global_agents):
                return False
        return True
    return _single_agent_exists(name, project_agents, global_agents)


def _single_agent_exists(name: str, project_agents: Path, global_agents: Path) -> bool:
    """단일 에이전트 이름 실존 검사 (디렉토리 lookup)."""
    return (project_agents / f"{name}.md").is_file() or (global_agents / f"{name}.md").is_file()


def check_matrix(
    matrix_path: Path,
    *,
    project_agents: Path,
    global_agents: Path,
) -> list[MatrixRow]:
    """매트릭스 파싱 + 참조 정합성 검증. 위반 시 MatrixError.

    I-5: 에러 메시지에 row.work_type + 컬럼명(primary/secondary) 포함.
    """
    rows = parse_matrix_table(matrix_path)
    # I-5: (work_type, 컬럼명, 참조명) 튜플로 위치 정보 보존
    missing: list[tuple[str, str, str]] = []
    for row in rows:
        if not _agent_exists(row.primary, project_agents, global_agents):
            missing.append((row.work_type, "primary", row.primary))
        if not _agent_exists(row.secondary, project_agents, global_agents):
            missing.append((row.work_type, "secondary", row.secondary))
    if missing:
        detail = ", ".join(f"행={wt!r} 컬럼={col} 참조={ref!r}" for wt, col, ref in missing)
        raise MatrixError(f"실존하지 않는 에이전트 참조: {detail}")
    return rows
