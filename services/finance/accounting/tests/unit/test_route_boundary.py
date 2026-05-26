"""OE002: route는 Repository를 직접 import/인스턴스화 하지 않는다."""

from __future__ import annotations

from pathlib import Path

ROUTES_DIR = Path(__file__).resolve().parents[2] / "oneerp_accounting_app" / "routes"


def test_journal_entries_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "journal_entries.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text


def test_accounts_receivable_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "accounts_receivable.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text
