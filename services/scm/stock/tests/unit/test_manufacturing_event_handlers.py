"""제조 이벤트 핸들러 단위 테스트 — 자재출고/작업완료 이벤트 처리 검증."""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any, cast
from unittest.mock import MagicMock, patch


def _make_material_issued_data(
    work_order_id: str,
    items: list[dict[str, Any]],
    tenant_id: str = "test",
) -> dict:
    """테스트용 MATERIAL_ISSUED EventEnvelope 데이터를 생성한다."""
    return {
        "event": {
            "doc_id": work_order_id,
            "tenant_id": tenant_id,
            "data": {
                "work_order_id": work_order_id,
                "items": items,
                "tenant_id": tenant_id,
            },
        },
    }


def _make_work_order_completed_data(
    work_order_id: str,
    item_code: str,
    produced_qty: float,
    tenant_id: str = "test",
) -> dict:
    """테스트용 WORK_ORDER_COMPLETED EventEnvelope 데이터를 생성한다."""
    return {
        "event": {
            "doc_id": work_order_id,
            "tenant_id": tenant_id,
            "data": {
                "work_order_id": work_order_id,
                "item_code": item_code,
                "produced_qty": produced_qty,
                "tenant_id": tenant_id,
            },
        },
    }


def test_자재출고_이벤트_처리() -> None:
    """MATERIAL_ISSUED 이벤트 수신 시 자재별 재고 차감(process_material_issue)이 호출되는지 검증."""
    issued_items = [
        {"item_code": "MAT-001", "issued_qty": 10.0},
        {"item_code": "MAT-002", "issued_qty": 5.0},
    ]
    event_data = _make_material_issued_data("WO-001", issued_items)

    with patch("oneerp_stock_app.services.stock_ledger_service.StockLedgerService") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        handlers = cast("Any", import_module("oneerp_stock_app.events.handlers"))

        asyncio.run(handlers.handle_material_issued(event_data, "evt-mfg-001"))

        mock_cls.assert_called_once_with("test")
        mock_instance.process_material_issue.assert_called_once_with(
            "WO-001",
            issued_items,
        )


def test_작업완료_이벤트_처리() -> None:
    """WORK_ORDER_COMPLETED 이벤트 수신 시 완제품 입고(process_production_receipt)가 호출되는지 검증."""
    event_data = _make_work_order_completed_data("WO-002", "FG-ITEM-001", 100.0)

    with patch("oneerp_stock_app.services.stock_ledger_service.StockLedgerService") as mock_cls:
        mock_instance = MagicMock()
        mock_cls.return_value = mock_instance

        handlers = cast("Any", import_module("oneerp_stock_app.events.handlers"))

        asyncio.run(handlers.handle_work_order_completed(event_data, "evt-mfg-002"))

        mock_cls.assert_called_once_with("test")
        mock_instance.process_production_receipt.assert_called_once_with(
            "WO-002",
            "FG-ITEM-001",
            100.0,
        )
