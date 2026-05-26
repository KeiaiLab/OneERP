from __future__ import annotations

from scripts.ci.normalize_g5_docs import (
    MANUAL_SECTIONS,
    manual_status,
    render_manual,
    render_tutorial,
    render_uat,
    tutorial_status,
    uat_status,
)


def test_render_manual_satisfies_g5_1_shape(tmp_path) -> None:
    path = tmp_path / "manual.md"
    path.write_text(render_manual("selling", ["기존 사용자 메모"]), encoding="utf-8")

    lines, sections, images = manual_status(path)

    assert lines >= 250
    assert sections == len(MANUAL_SECTIONS)
    assert images >= 5


def test_render_tutorial_satisfies_g5_2_shape(tmp_path) -> None:
    path = tmp_path / "tutorial.md"
    path.write_text(render_tutorial("selling", ["기존 튜토리얼 메모"]), encoding="utf-8")

    lines, code_blocks = tutorial_status(path)

    assert lines >= 300
    assert code_blocks >= 10


def test_render_uat_satisfies_g5_3_shape(tmp_path) -> None:
    path = tmp_path / "uat.md"
    path.write_text(render_uat("selling", ["기존 UAT 메모"]), encoding="utf-8")

    status = uat_status(path)

    assert status["uat_lines"] >= 200
    assert status["frontmatter_fields"] == 3
    assert status["uat_scenarios"] >= 5
    assert status["approval_signed"] == 1
    assert status["test_data_cleanup"] == 1
