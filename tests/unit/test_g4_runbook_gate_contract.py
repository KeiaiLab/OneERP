from __future__ import annotations

from pathlib import Path

from scripts.audit.gates import module_runbook_path
from scripts.ci.normalize_g4_runbooks import REQUIRED_SECTIONS, render_runbook


def test_module_runbook_path_is_module_specific_for_merged_modules() -> None:
    assert module_runbook_path("consolidation") == Path("docs/ops/runbook-consolidation.md")
    assert module_runbook_path("mail") == Path("docs/ops/runbook-mail.md")
    assert module_runbook_path("messenger") == Path("docs/ops/runbook-messenger.md")
    assert module_runbook_path("quality") == Path("docs/ops/runbook-quality.md")
    assert module_runbook_path("subscriptions") == Path("docs/ops/runbook-subscriptions.md")


def test_render_runbook_satisfies_g4_2_shape() -> None:
    text = render_runbook("selling", ["기존 진단 메모"])

    assert text.count("\n") + 1 >= 150
    assert "owner:" in text
    assert "module: selling" in text
    assert "last_reviewed:" in text
    for section in REQUIRED_SECTIONS:
        assert f"## {section}" in text
