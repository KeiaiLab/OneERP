from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "oneerp_gateway_app" / "routes"


def test_auth_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROOT / "auth.py").read_text(encoding="utf-8")
    assert "Repository(" not in text
    assert "from oneerp_core.repository" not in text


def test_users_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROOT / "users.py").read_text(encoding="utf-8")
    assert "Repository(" not in text
    assert "from oneerp_core.repository" not in text


def test_me_route는_repository를_직접_사용하지_않는다() -> None:
    text = (ROOT / "me.py").read_text(encoding="utf-8")
    assert "Repository(" not in text
    assert "from oneerp_core.repository" not in text
