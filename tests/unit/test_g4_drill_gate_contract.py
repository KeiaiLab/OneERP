from __future__ import annotations

from scripts.ci.normalize_g4_drills import REQUIRED_SECTIONS, render_drill


def test_render_drill_satisfies_g4_drill_shape() -> None:
    text = render_drill("G4-3", "selling", ["기존 복구 메모"])

    assert text.count("\n") + 1 >= 150
    assert "gate: G4-3" in text
    assert "module: selling" in text
    assert "drill_date:" in text
    assert "scenario:" in text
    assert "evidence:" in text
    for section in REQUIRED_SECTIONS:
        assert f"## {section}" in text


def test_render_drill_uses_gate_specific_scenario() -> None:
    rollback = render_drill("G4-4", "ecommerce", [])
    oncall = render_drill("G4-5", "ecommerce", [])

    assert "release-rollback-rehearsal" in rollback
    assert "p2-incident-response-rehearsal" in oncall
