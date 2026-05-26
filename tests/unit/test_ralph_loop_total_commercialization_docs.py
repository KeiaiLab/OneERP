from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ralph_loop_prompt가_전체_상용_완성_계약을_명시한다() -> None:
    text = (ROOT / "RALPH-LOOP-PROMPT.md").read_text(encoding="utf-8")
    assert "1,081" in text
    assert "47모듈" in text
    assert "run_total_commercial_gate.sh" in text
    assert ".reports[]" in text
    assert "Wave 1 × 23/23 전수 PASS" not in text  # noqa: RUF001 — 과거 프롬프트 문구의 역설 검증


def test_progress_md가_최종_목표를_1081셀로_적는다() -> None:
    text = (ROOT / "PROGRESS.md").read_text(encoding="utf-8")
    assert "1,081" in text
    assert "47모듈" in text
    assert "276 셀" not in text


def test_handoff_md가_예상_소요를_실제_산술로_적는다() -> None:
    text = (ROOT / "HANDOFF.md").read_text(encoding="utf-8")
    assert "960 시간" in text
    assert "40일" in text
    assert "약 80 시간" not in text
