"""포괄주문(Blanket Order) 엔드포인트 테스트.

Route → Service 분리 후 BlanketOrderService 를 mock 한다.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_selling_app.main import app

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

_BASE_URL = "/api/v1/blanket-orders"


@patch("oneerp_selling_app.routes.blanket_orders.BlanketOrderService")
def test_포괄주문_생성_정상(mock_service_cls: MagicMock) -> None:
    """POST /api/v1/blanket-orders -- 정상 생성 시 201을 반환한다."""
    service = MagicMock()
    service.create_from_request.return_value = {
        "id": "BLO-2026-00001",
        "message": "포괄주문이 생성되었습니다",
    }
    mock_service_cls.return_value = service

    response = client.post(
        _BASE_URL,
        json={
            "customer": "CUST-001",
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "테스트 품목",
                    "qty": 100.0,
                    "rate": 5000.0,
                    "ordered_qty": 0.0,
                },
            ],
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "BLO-2026-00001"


@patch("oneerp_selling_app.routes.blanket_orders.BlanketOrderService")
def test_포괄주문_목록_조회(mock_service_cls: MagicMock) -> None:
    """GET /api/v1/blanket-orders -- 페이지네이션 응답 구조를 확인한다."""
    service = MagicMock()
    service.list_orders.return_value = {
        "data": [{"_id": "BLO-001", "customer": "CUST-001"}],
        "total": 1,
    }
    mock_service_cls.return_value = service

    response = client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["data"]) == 1


@patch("oneerp_selling_app.routes.blanket_orders.BlanketOrderService")
def test_포괄주문_조회_404(mock_service_cls: MagicMock) -> None:
    """GET /api/v1/blanket-orders/{doc_id} -- 없는 문서는 404를 반환한다."""
    service = MagicMock()
    service.get_order.return_value = None
    mock_service_cls.return_value = service

    response = client.get(f"{_BASE_URL}/NONEXISTENT")
    assert response.status_code == 404
