from __future__ import annotations

from pathlib import Path

from scripts.roadmap.status_render import ModuleRow, RenderContext, render_section

ROOT = Path(__file__).resolve().parents[2]


def test_progress_섹션은_1081_분모를_사용한다() -> None:
    modules = [ModuleRow(module="demo", label="alpha", passed=23, failed=0, implemented=23)]
    ctx = RenderContext(modules=modules, waves=[], active_wave=1)
    text = render_section("progress", ctx)
    assert "1081" in text


def test_status_md가_출시와_정지_자동섹션을_가진다() -> None:
    text = (ROOT / "docs/product/roadmap/status.md").read_text(encoding="utf-8")
    assert "<!-- status-auto:release-rehearsal -->" in text
    assert "<!-- status-auto:blockers -->" in text


def test_release_rehearsal_섹션은_미실행_상태를_보여준다() -> None:
    ctx = RenderContext(modules=[], waves=[], active_wave=1)
    text = render_section("release-rehearsal", ctx)
    assert "미실행" in text
    assert "artifacts/rehearsal/latest/" in text


def test_blockers_섹션은_hand_off_상태를_명시한다() -> None:
    ctx = RenderContext(modules=[], waves=[], active_wave=1)
    text = render_section("blockers", ctx)
    assert "상태 원문" in text
    assert "Pre-Loop Cleanup 완료" in text
    assert "판정" in text
    assert "블로커 0건" in text
