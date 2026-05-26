from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "oneerp_expenses_app" / "routes"


def _assert_route_uses_service_boundary(filename: str) -> None:
    text = (ROOT / filename).read_text(encoding="utf-8")
    assert "Repository(" not in text
    assert "from oneerp_core.repository" not in text


def test_expense_claims_route는_repository를_직접_사용하지_않는다() -> None:
    _assert_route_uses_service_boundary("expense_claims.py")


def test_expense_types_route는_repository를_직접_사용하지_않는다() -> None:
    _assert_route_uses_service_boundary("expense_types.py")


def test_corporate_cards_route는_repository를_직접_사용하지_않는다() -> None:
    _assert_route_uses_service_boundary("corporate_cards.py")


def test_corporate_card_transactions_route는_repository를_직접_사용하지_않는다() -> None:
    _assert_route_uses_service_boundary("corporate_card_transactions.py")


def test_travel_requests_route는_repository를_직접_사용하지_않는다() -> None:
    _assert_route_uses_service_boundary("travel_requests.py")
