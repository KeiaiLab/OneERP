from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "oneerp_calendar_app" / "routes"


def test_resource_bookings_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROOT / "resource_bookings.py").read_text(encoding="utf-8")
    assert "Repository(" not in text
    assert "from oneerp_core.repository" not in text
