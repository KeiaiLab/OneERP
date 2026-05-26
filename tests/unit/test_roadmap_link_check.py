from __future__ import annotations

import importlib
from pathlib import Path

link_check = importlib.import_module("scripts.roadmap.link_check")


def test_reverse_scan는_docs_plans을_exclude한다(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path
    plans_dir = repo / "docs" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "plan.md").write_text(
        "docs/product/roadmap/status.md 를 참조한다.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(link_check, "REPO", repo)
    monkeypatch.setattr(link_check, "REVERSE_SCAN_DIRS", (plans_dir,))
    monkeypatch.setattr(link_check, "REVERSE_EXCLUDES", (repo / "docs" / "plans",))

    assert link_check.check_reverse(verbose=False) == []
