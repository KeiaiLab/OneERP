"""Stock 이벤트 핸들러 단위 테스트."""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any, cast
from unittest.mock import MagicMock, patch


def _make_event_data(doc_id: str, tenant_id: str = "test") -> dict:
    """테스트용 EventEnvelope 데이터를 생성한다."""
    return {"event": {"doc_id": doc_id, "tenant_id": tenant_id}}


def test_판매주문_이벤트_재고예약_호출() -> None:
    """판매주문 제출 이벤트 수신 시 재고 예약 서비스가 호출되는지 검증."""
    event_data = _make_event_data("SO-001")

    with patch(
        "oneerp_stock_app.services.stock_reservation_service.StockReservationService"
    ) as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        handlers = cast("Any", import_module("oneerp_stock_app.events.handlers"))

        asyncio.run(handlers.handle_sales_order_submitted(event_data, "evt-001"))

        mock_cls.assert_called_once_with("test")
        mock_instance.reserve_for_sales_order.assert_called_once_with("SO-001")


def test_납품서_이벤트_재고차감_호출() -> None:
    """납품서 제출 이벤트 수신 시 재고 차감 + 예약 해제가 호출되는지 검증."""
    event_data = _make_event_data("DN-001")

    with (
        patch(
            "oneerp_stock_app.services.stock_ledger_service.StockLedgerService"
        ) as mock_ledger_cls,
        patch(
            "oneerp_stock_app.services.stock_reservation_service.StockReservationService"
        ) as mock_rsv_cls,
    ):
        mock_ledger = MagicMock()
        mock_ledger_cls.return_value = mock_ledger
        mock_rsv = MagicMock()
        mock_rsv_cls.return_value = mock_rsv

        handlers = cast("Any", import_module("oneerp_stock_app.events.handlers"))

        asyncio.run(handlers.handle_delivery_note_submitted(event_data, "evt-002"))

        mock_ledger_cls.assert_called_once_with("test")
        mock_ledger.process_delivery.assert_called_once_with("DN-001")
        mock_rsv_cls.assert_called_once_with("test")
        mock_rsv.release_reservation.assert_called_once_with("DN-001")


def test_입고전표_이벤트_재고증가_호출() -> None:
    """입고전표 제출 이벤트 수신 시 재고 증가가 호출되는지 검증."""
    event_data = _make_event_data("PR-001")

    with patch("oneerp_stock_app.services.stock_ledger_service.StockLedgerService") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        handlers = cast("Any", import_module("oneerp_stock_app.events.handlers"))

        asyncio.run(handlers.handle_purchase_receipt_submitted(event_data, "evt-003"))

        mock_cls.assert_called_once_with("test")
        mock_instance.process_receipt.assert_called_once_with("PR-001")


def test_재고이동_이벤트_재고원장_반영_호출() -> None:
    """재고이동 제출 이벤트 수신 시 재고 원장 반영이 호출되는지 검증."""
    event_data = _make_event_data("STE-001")

    with patch("oneerp_stock_app.services.stock_ledger_service.StockLedgerService") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        handlers = cast("Any", import_module("oneerp_stock_app.events.handlers"))

        asyncio.run(handlers.handle_stock_entry_submitted(event_data, "evt-004"))

        mock_cls.assert_called_once_with("test")
        mock_instance.process_stock_entry.assert_called_once_with("STE-001")
