from __future__ import annotations

from pathlib import Path

import pytest

from scripts.agents.routing import RouteNotFoundError, RoutingDecision, route

MATRIX = """\
# 매트릭스

## 표

| 작업 유형                            | 호출자             | 1차 에이전트          | 2차 위임 | Stage skip          |
|--------------------------------------|--------------------|----------------------|----------|---------------------|
| BE+FE 동시 (일반 PR)                 | 사용자/auto-cycle  | oe-feature-pipeliner | sub-x    | —                   |
| FE only (일반 PR)                    | 사용자/auto-cycle  | oe-feature-pipeliner | —        | be,typebridge       |
| Commercial Engine wave               | /commercial-engine | ce-planner           | —        | —                   |
"""


@pytest.fixture
def matrix_file(tmp_path: Path) -> Path:
    p = tmp_path / "_routing-matrix.md"
    p.write_text(MATRIX, encoding="utf-8")
    return p


def test_BE_FE_사용자_호출은_pipeliner로_라우팅(matrix_file: Path) -> None:
    decision = route(matrix_file, work_type="BE+FE 동시 (일반 PR)", caller="사용자")
    assert decision == RoutingDecision(
        primary="oe-feature-pipeliner",
        secondary="sub-x",
        skip_stages=frozenset(),
    )


def test_FE_only는_be_typebridge_skip(matrix_file: Path) -> None:
    decision = route(matrix_file, work_type="FE only (일반 PR)", caller="auto-cycle")
    assert decision.primary == "oe-feature-pipeliner"
    assert decision.skip_stages == {"be", "typebridge"}


def test_commercial_engine은_ce_planner(matrix_file: Path) -> None:
    decision = route(
        matrix_file,
        work_type="Commercial Engine wave",
        caller="/commercial-engine",
    )
    assert decision.primary == "ce-planner"


def test_매트릭스에_없는_조합은_RouteNotFoundError(matrix_file: Path) -> None:
    with pytest.raises(RouteNotFoundError, match="라우팅 행 없음"):
        route(matrix_file, work_type="없는 작업", caller="사용자")


def test_프로젝트_매트릭스_BE_FE_라우팅() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    matrix = repo_root / ".claude" / "agents" / "_routing-matrix.md"
    decision = route(matrix, work_type="BE+FE 동시 (일반 PR)", caller="사용자")
    assert decision.primary == "oe-feature-pipeliner"
