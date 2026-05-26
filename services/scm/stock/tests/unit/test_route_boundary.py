"""OE002: route는 Repository를 직접 import/인스턴스화 하지 않는다."""

from __future__ import annotations

from pathlib import Path

ROUTES_DIR = Path(__file__).resolve().parents[2] / "oneerp_stock_app" / "routes"


def test_items_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "items.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text


def test_purchase_receipts_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "purchase_receipts.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text
