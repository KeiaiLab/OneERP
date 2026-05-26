from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "oneerp_wiki_app" / "routes"


def test_wiki_pages_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROOT / "wiki_pages.py").read_text(encoding="utf-8")
    assert "Repository(" not in text
    assert "from oneerp_core.repository" not in text
