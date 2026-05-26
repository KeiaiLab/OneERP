"""OE002: route는 Repository를 직접 import/인스턴스화 하지 않는다."""

from __future__ import annotations

from pathlib import Path

ROUTES_DIR = Path(__file__).resolve().parents[2] / "oneerp_selling_app" / "routes"


def test_sales_orders_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "sales_orders.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text, "route는 service 계층을 거쳐야 함"
    assert "Repository(" not in text, "route는 Repository를 직접 인스턴스화하지 말 것"


def test_delivery_notes_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "delivery_notes.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text


def test_sales_invoices_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROUTES_DIR / "sales_invoices.py").read_text(encoding="utf-8")
    assert "from oneerp_core.repository" not in text
    assert "Repository(" not in text
