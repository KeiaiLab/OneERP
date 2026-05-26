"""라우팅 매트릭스 → 결정 함수.

매트릭스 markdown 표를 읽어 (작업 유형, 호출자) 입력에 대한 1차 에이전트·
2차 위임·Stage skip을 결정한다. T2의 parse_matrix_table을 재사용해 표 파싱
경계 조건(false positive, EOF, 컬럼 부족 등)을 일관되게 처리.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from scripts.agents.check_matrix_consistency import (
    DASH,
    MatrixRow,
    parse_matrix_table,
)


class RouteNotFoundError(LookupError):
    """매트릭스에 매치되는 행이 없을 때."""


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    primary: str
    secondary: str
    skip_stages: frozenset[str] = field(default_factory=frozenset)


def _caller_matches(row_caller: str, caller: str) -> bool:
    """행의 호출자 컬럼이 입력 호출자를 포함하는가.

    예: row_caller="사용자/auto-cycle", caller="auto-cycle" → True.
    예: row_caller="/commercial-engine", caller="/commercial-engine" → True.
    `/`로 시작하는 셀은 단일 경로 이름이므로 분리하지 않고 전체를 후보로 사용.
    일반 셀은 `/` 구분자로 분리해 각 항목을 후보로 사용.
    공백 변종은 strip만 적용.
    """
    stripped = row_caller.strip()
    if stripped.startswith("/"):
        # 단일 경로 식별자 — 분리 없이 전체 비교
        candidates: frozenset[str] = frozenset({stripped})
    else:
        candidates = frozenset({c.strip() for c in stripped.split("/") if c.strip()})
    return caller.strip() in candidates


def _parse_skip(skip_cell: str) -> frozenset[str]:
    """Stage skip 셀을 frozenset으로 파싱. DASH 시 빈 frozenset."""
    if skip_cell.strip() in DASH:
        return frozenset()
    return frozenset(s.strip() for s in skip_cell.split(",") if s.strip())


def route(matrix_path: Path, *, work_type: str, caller: str) -> RoutingDecision:
    """매트릭스에서 (work_type, caller) 매치 행을 찾아 결정 반환.

    동일 조합 행이 2개 이상이면 *첫 번째*를 반환 (안정적 결정). 0개면
    RouteNotFoundError.
    """
    rows: list[MatrixRow] = parse_matrix_table(matrix_path)
    target_work = work_type.strip()
    for row in rows:
        if row.work_type.strip() == target_work and _caller_matches(row.caller, caller):
            return RoutingDecision(
                primary=row.primary,
                secondary=row.secondary,
                skip_stages=_parse_skip(row.skip),
            )
    raise RouteNotFoundError(f"라우팅 행 없음: work_type={work_type!r}, caller={caller!r}")
