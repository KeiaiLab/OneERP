"""OE005: reservation 하위 서브컨텍스트 간 직접 import를 금지한다."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "oneerp_reservation_app"


def _read_package_files(package: str) -> list[Path]:
    return sorted((ROOT / package).rglob("*.py"))


def _assert_no_direct_imports(package: str, forbidden: str) -> None:
    for path in _read_package_files(package):
        text = path.read_text(encoding="utf-8")
        assert forbidden not in text, f"{path} 에서 {forbidden} 직접 import 금지"


def test_reservation은_rental을_직접_import하지_않는다() -> None:
    _assert_no_direct_imports("reservation", "oneerp_reservation_app.rental")


def test_rental은_reservation을_직접_import하지_않는다() -> None:
    _assert_no_direct_imports("rental", "oneerp_reservation_app.reservation")


def test_root_main은_통합_조립_import를_허용한다() -> None:
    text = (ROOT / "main.py").read_text(encoding="utf-8")
    assert "from .rental.entities import ENTITY_METAS as RENTAL_ENTITY_METAS" in text
    assert "from .reservation.entities import ENTITY_METAS as RES_ENTITY_METAS" in text
