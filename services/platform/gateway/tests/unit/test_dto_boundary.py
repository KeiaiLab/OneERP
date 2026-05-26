from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "oneerp_gateway_app"


def test_user_dto가_dto_py에_존재한다() -> None:
    text = (ROOT / "dto.py").read_text(encoding="utf-8")
    assert "class UserCreate" in text
    assert "class UserUpdate" in text


def test_user_model에는_request_dto가_없다() -> None:
    text = (ROOT / "models" / "user.py").read_text(encoding="utf-8")
    assert "class UserCreate" not in text
    assert "class UserUpdate" not in text
