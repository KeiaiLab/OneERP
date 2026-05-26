"""재고원장(Stock Ledger Entry) 내부 연계 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_stock_app.routes.stock_ledger_entries as _mod
from fastapi.testclient import TestClient
from oneerp_stock_app.main import app as stock_app

client = TestClient(stock_app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)


def test_구매입고에서_재고원장_생성_정상(monkeypatch: object) -> None:
    """POST /api/v1/stock-ledger-entries/from-purchase-receipt — 이벤트 payload로 원장을 생성한다."""
    service = MagicMock()
    service.process_receipt_payload.return_value = ["SLE-001", "SLE-002"]
    monkeypatch.setattr(_mod, "_get_stock_ledger_service", lambda tenant_id: service)  # type: ignore[attr-defined]

    response = client.post(
        "/api/v1/stock-ledger-entries/from-purchase-receipt",
        json={
            "receipt_id": "PR-001",
            "tenant_id": "test-tenant",
            "items": [
                {"item_code": "ITEM-001", "qty": 3, "rate": 1200, "warehouse": "WH-01"},
                {"item_code": "ITEM-002", "qty": 1, "rate": 900, "warehouse": "WH-01"},
            ],
        },
    )

    assert response.status_code == 201
    assert response.json() == {
        "receipt_id": "PR-001",
        "stock_ledger_entry_ids": ["SLE-001", "SLE-002"],
        "message": "구매입고 기준 재고원장이 생성되었습니다",
    }
    service.process_receipt_payload.assert_called_once_with(
        "PR-001",
        [
            {"item_code": "ITEM-001", "qty": 3, "rate": 1200, "warehouse": "WH-01"},
            {"item_code": "ITEM-002", "qty": 1, "rate": 900, "warehouse": "WH-01"},
        ],
    )
