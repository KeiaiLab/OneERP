"""구매주문(PurchaseOrder) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_buying_app.main import app
from oneerp_core.events.schemas import EventType

client = TestClient(app)
client.headers.update(
    {
        "X-Tenant-Id": "test-tenant",
        "X-User-Sub": "test-user",
        "X-User-Roles": "admin",
        "X-User-Permissions": "*:*",
        "X-User-Tier": "super_admin",
    }
)


@patch("oneerp_buying_app.routes.purchase_orders.PurchasePricingService")
@patch("oneerp_buying_app.routes.purchase_orders._get_repo")
@patch("oneerp_buying_app.routes.purchase_orders.generate_name", return_value="PO-2026-00001")
def test_구매주문_생성_정상(
    mock_name: MagicMock, mock_repo: MagicMock, mock_pricing: MagicMock
) -> None:
    """POST /api/v1/purchase-orders -- 정상 생성 시 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    mock_pricing.return_value.apply_rules.return_value = {
        "total_discount": 0,
        "rules_applied": [],
    }
    response = client.post(
        "/api/v1/purchase-orders",
        json={
            "supplier_id": "SUP-001",
            "supplier_name": "테스트 공급업체",
            "transaction_date": "2026-03-17",
            "items": [
                {"item_code": "ITEM-001", "item_name": "원자재A", "qty": 10, "rate": 5000},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "PO-2026-00001"
    inserted = mock_repo.return_value.insert.call_args.args[0]
    assert inserted["items"][0]["delivery_date"] == date(2026, 3, 17).isoformat()


@patch("oneerp_buying_app.routes.purchase_orders._get_repo")
def test_구매주문_목록_조회(mock_repo: MagicMock) -> None:
    """GET /api/v1/purchase-orders -- 페이지네이션 응답 구조를 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "PO-001", "supplier_name": "업체"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get("/api/v1/purchase-orders?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1


@patch("oneerp_buying_app.routes.purchase_orders._get_repo")
def test_구매주문_상세_조회_미존재_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/purchase-orders/{doc_id} -- 없는 구매주문은 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get("/api/v1/purchase-orders/NOT-EXIST")
    assert response.status_code == 404


@patch("oneerp_buying_app.routes.purchase_orders._get_purchase_invoice_repo")
@patch("oneerp_buying_app.routes.purchase_orders._get_purchase_receipt_repo")
@patch("oneerp_buying_app.routes.purchase_orders._get_repo")
def test_구매주문_상세는_미결수량과_하위문서요약을_반환한다(
    mock_repo: MagicMock,
    mock_receipt_repo: MagicMock,
    mock_invoice_repo: MagicMock,
) -> None:
    """GET /api/v1/purchase-orders/{doc_id} -- 발주 진행 요약을 함께 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {
        "_id": "PO-001",
        "docstatus": 1,
        "transaction_date": "2026-03-17",
        "items": [
            {
                "item_code": "ITEM-001",
                "item_name": "원자재A",
                "qty": 10,
                "rate": 5000,
                "amount": 50000,
                "received_qty": 4,
                "delivery_date": "2026-03-20",
            }
        ],
    }
    mock_repo.return_value = repo
    mock_receipt_repo.return_value.count.side_effect = lambda query=None: {
        0: 1,
        1: 2,
    }[(query or {}).get("docstatus", 0)]
    mock_invoice_repo.return_value.count.side_effect = lambda query=None: {
        0: 1,
        1: 0,
    }[(query or {}).get("docstatus", 0)]

    response = client.get("/api/v1/purchase-orders/PO-001")

    assert response.status_code == 200
    data = response.json()
    assert data["status_badge"] == "partially_received"
    assert data["remaining_qty"] == 6.0
    assert data["receipt_completion_percent"] == 40.0
    assert data["next_delivery_date"] == "2026-03-20"
    assert data["downstream_summary"] == {
        "purchase_receipt_draft_count": 1,
        "purchase_receipt_submitted_count": 2,
        "purchase_invoice_draft_count": 1,
        "purchase_invoice_submitted_count": 0,
        "has_downstream_documents": True,
    }


@patch("oneerp_buying_app.routes.purchase_orders._get_repo")
def test_구매주문_제출_이벤트_발행(mock_repo: MagicMock) -> None:
    """POST /api/v1/purchase-orders/{doc_id}/submit -- submit_with_event 호출을 검증한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = {"_id": "PO-001", "docstatus": 0}
    repo.submit_with_event.return_value = True
    mock_repo.return_value = repo
    response = client.post("/api/v1/purchase-orders/PO-001/submit")
    assert response.status_code == 200
    repo.submit_with_event.assert_called_once()
    call_args = repo.submit_with_event.call_args
    # 위치 인자: doc_id
    assert call_args[0][0] == "PO-001"
    # 키워드 인자: event_type
    assert call_args[1]["event_type"] == EventType.PURCHASE_ORDER_SUBMITTED
    # 키워드 인자: event_data
    assert call_args[1]["event_data"] == {"doc_id": "PO-001"}
