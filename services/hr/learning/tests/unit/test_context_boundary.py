"""OE005: learning 하위 서브컨텍스트 간 직접 import를 금지한다."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "oneerp_learning_app"


def _read_package_files(package: str) -> list[Path]:
    return sorted((ROOT / package).rglob("*.py"))


def _assert_no_direct_imports(package: str, forbidden: str) -> None:
    for path in _read_package_files(package):
        text = path.read_text(encoding="utf-8")
        assert forbidden not in text, f"{path} 에서 {forbidden} 직접 import 금지"


def test_lms는_workreport를_직접_import하지_않는다() -> None:
    _assert_no_direct_imports("lms", "oneerp_learning_app.workreport")


def test_workreport는_lms를_직접_import하지_않는다() -> None:
    _assert_no_direct_imports("workreport", "oneerp_learning_app.lms")


def test_root_main은_통합_조립_import를_허용한다() -> None:
    text = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "from .lms.entities import ENTITY_METAS as LMS_ENTITY_METAS" in text
    assert "from .workreport.entities import ENTITY_METAS as WR_ENTITY_METAS" in text
