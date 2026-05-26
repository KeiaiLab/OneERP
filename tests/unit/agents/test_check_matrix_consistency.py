from __future__ import annotations

from pathlib import Path

import pytest

from scripts.agents.check_matrix_consistency import (
    MatrixError,
    check_matrix,
    parse_matrix_table,
)

MATRIX_TEMPLATE = """\
# 매트릭스

## 표

| 작업 유형 | 호출자 | 1차 에이전트          | 2차 위임 | Stage skip |
|-----------|--------|----------------------|----------|------------|
| BE+FE     | 사용자 | oe-feature-pipeliner | sub-x    | —          |
| FE only   | 사용자 | oe-feature-pipeliner | —        | be         |
"""


def _make_agents(root: Path, names: list[str]) -> None:
    for n in names:
        (root / f"{n}.md").write_text(
            f"---\nname: {n}\ndescription: x\ntools: Read\nmodel: sonnet\n---\n",
            encoding="utf-8",
        )


def test_매트릭스_모든_참조가_실존하면_PASS(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    matrix = project / "_routing-matrix.md"
    matrix.write_text(MATRIX_TEMPLATE, encoding="utf-8")
    _make_agents(project, ["oe-feature-pipeliner"])
    global_root = tmp_path / "global"
    global_root.mkdir()
    _make_agents(global_root, ["sub-x"])
    check_matrix(matrix, project_agents=project, global_agents=global_root)


def test_누락_에이전트는_MatrixError(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    matrix = project / "_routing-matrix.md"
    matrix.write_text(MATRIX_TEMPLATE, encoding="utf-8")
    # oe-feature-pipeliner 없음
    global_root = tmp_path / "global"
    global_root.mkdir()
    with pytest.raises(MatrixError, match="oe-feature-pipeliner"):
        check_matrix(matrix, project_agents=project, global_agents=global_root)


def test_표가_없으면_MatrixError(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    matrix = project / "_routing-matrix.md"
    matrix.write_text("# 비어있음\n", encoding="utf-8")
    with pytest.raises(MatrixError, match="표"):
        parse_matrix_table(matrix)


def test_표_분류_헤딩이_먼저_있어도_실제_매트릭스를_파싱한다(tmp_path: Path) -> None:
    """## 표 분류 같은 헤딩이 앞에 있어도 실제 ## 표를 정확히 잡는다 (I-1+I-3)."""
    project = tmp_path / "project"
    project.mkdir()
    matrix = project / "_routing-matrix.md"
    # ## 표 분류 헤딩이 먼저 나오고 이후 실제 ## 표 등장
    matrix.write_text(
        "# 매트릭스\n"
        "\n"
        "## 표 분류\n"
        "\n"
        "| 분류 | 설명 |\n"
        "|------|------|\n"
        "| A    | x    |\n"
        "\n" + MATRIX_TEMPLATE.split("# 매트릭스")[1],  # 실제 ## 표 본문 포함
        encoding="utf-8",
    )
    _make_agents(project, ["oe-feature-pipeliner"])
    global_root = tmp_path / "global"
    global_root.mkdir()
    _make_agents(global_root, ["sub-x"])
    rows = check_matrix(matrix, project_agents=project, global_agents=global_root)
    assert len(rows) == 2  # MATRIX_TEMPLATE의 데이터 2행


def test_EOF에_개행_없어도_마지막_행을_파싱한다(tmp_path: Path) -> None:
    """파일 마지막 행에 \\n 없어도 마지막 데이터 행이 누락되지 않는다 (I-2)."""
    project = tmp_path / "project"
    project.mkdir()
    matrix = project / "_routing-matrix.md"
    # 마지막 \n 제거
    matrix.write_text(MATRIX_TEMPLATE.rstrip("\n"), encoding="utf-8")
    rows = parse_matrix_table(matrix)
    assert len(rows) == 2  # 마지막 행 누락 X


def test_컬럼_수_부족_행은_MatrixError(tmp_path: Path) -> None:
    """5셀 미만 행은 silent skip 대신 MatrixError (I-4)."""
    project = tmp_path / "project"
    project.mkdir()
    matrix = project / "_routing-matrix.md"
    matrix.write_text(
        "## 표\n"
        "\n"
        "| 작업 유형 | 호출자 | 1차 | 2차 | skip |\n"
        "|-----------|--------|-----|-----|------|\n"
        "| BE+FE     | 사용자 | x   | y   |\n",  # 컬럼 4개 (5 미만)
        encoding="utf-8",
    )
    with pytest.raises(MatrixError, match="컬럼 수 부족"):
        parse_matrix_table(matrix)


def test_누락_에이전트_에러에_행_컬럼_위치_포함(tmp_path: Path) -> None:
    """에러 메시지에 row.work_type과 컬럼명(primary/secondary) 포함 (I-5)."""
    project = tmp_path / "project"
    project.mkdir()
    matrix = project / "_routing-matrix.md"
    matrix.write_text(MATRIX_TEMPLATE, encoding="utf-8")
    # oe-feature-pipeliner / sub-x 모두 없음
    global_root = tmp_path / "global"
    global_root.mkdir()
    with pytest.raises(MatrixError) as exc_info:
        check_matrix(matrix, project_agents=project, global_agents=global_root)
    msg = str(exc_info.value)
    # work_type 포함 확인
    assert "BE+FE" in msg or "FE only" in msg
    # 컬럼명 포함 확인
    assert "primary" in msg or "secondary" in msg


def test_multi_agent_슬래시_표기도_정합_검증(tmp_path: Path) -> None:
    """ce-artisan/scribe/executor 같은 슬래시 묶음 — 모든 토큰이 실존하면 PASS."""
    project = tmp_path / "project"
    project.mkdir()
    matrix = project / "_routing-matrix.md"
    matrix.write_text(
        "## 표\n\n"
        "| 작업 유형 | 호출자 | 1차    | 2차                                | skip |\n"
        "|-----------|--------|--------|------------------------------------|------|\n"
        "| 작업 A    | 사용자 | ce-planner | ce-artisan/scribe/executor     | —    |\n",
        encoding="utf-8",
    )
    _make_agents(project, ["ce-planner", "ce-artisan", "ce-scribe", "ce-executor"])
    global_root = tmp_path / "global"
    global_root.mkdir()
    rows = check_matrix(matrix, project_agents=project, global_agents=global_root)
    assert len(rows) == 1


def test_multi_agent_슬래시_표기_일부_누락은_MatrixError(tmp_path: Path) -> None:
    """슬래시 묶음 토큰 중 하나라도 미존재면 MatrixError."""
    project = tmp_path / "project"
    project.mkdir()
    matrix = project / "_routing-matrix.md"
    matrix.write_text(
        "## 표\n\n"
        "| 작업 유형 | 호출자 | 1차    | 2차                                | skip |\n"
        "|-----------|--------|--------|------------------------------------|------|\n"
        "| 작업 A    | 사용자 | ce-planner | ce-artisan/scribe/missing      | —    |\n",
        encoding="utf-8",
    )
    _make_agents(project, ["ce-planner", "ce-artisan", "ce-scribe"])  # ce-missing 없음
    global_root = tmp_path / "global"
    global_root.mkdir()
    with pytest.raises(MatrixError, match="ce-artisan/scribe/missing"):
        check_matrix(matrix, project_agents=project, global_agents=global_root)


def test_multi_agent_표기_trailing_slash는_단일_매치(tmp_path: Path) -> None:
    """예: 'ce-artisan/' (trailing slash) → 단일 'ce-artisan' 검증."""
    project = tmp_path / "project"
    project.mkdir()
    matrix = project / "_routing-matrix.md"
    matrix.write_text(
        "## 표\n\n"
        "| 작업 유형 | 호출자 | 1차    | 2차      | skip |\n"
        "|-----------|--------|--------|----------|------|\n"
        "| 작업 A    | 사용자 | ce-planner | ce-artisan/ | —    |\n",
        encoding="utf-8",
    )
    _make_agents(project, ["ce-planner", "ce-artisan"])
    global_root = tmp_path / "global"
    global_root.mkdir()
    rows = check_matrix(matrix, project_agents=project, global_agents=global_root)
    assert len(rows) == 1


def test_프로젝트_라우팅_매트릭스가_정합한다() -> None:
    """OneErp/.claude/agents/_routing-matrix.md를 실제 검증한다."""
    repo_root = Path(__file__).resolve().parents[3]
    matrix = repo_root / ".claude" / "agents" / "_routing-matrix.md"
    project = repo_root / ".claude" / "agents"
    global_root = Path.home() / ".claude" / "agents"
    rows = check_matrix(matrix, project_agents=project, global_agents=global_root)
    assert len(rows) >= 10  # 최소 10행 이상
    primaries = {r.primary for r in rows}
    assert "oe-feature-pipeliner" in primaries
    assert "ce-planner" in primaries
