"""판매반품(Sales Return) 엔드포인트 테스트.

Route → Service 분리 후(arch-baseline 감소) SalesReturnService 를 mock 한다.
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

_BASE_URL = "/api/v1/sales-returns"


@patch("oneerp_selling_app.routes.sales_returns.SalesReturnService")
def test_판매반품_생성_정상(mock_service_cls: MagicMock) -> None:
    """POST /api/v1/sales-returns -- 정상 생성 시 201을 반환한다."""
    service = MagicMock()
    service.create_from_request.return_value = {
        "id": "SRT-2026-00001",
        "message": "판매반품이 생성되었습니다",
    }
    mock_service_cls.return_value = service

    response = client.post(
        _BASE_URL,
        json={
            "customer": "CUST-001",
            "return_date": "2026-03-18",
            "reason": "불량품",
            "items": [
                {
                    "item_code": "ITEM-001",
                    "item_name": "테스트 품목",
                    "qty": 2.0,
                    "rate": 10000.0,
                },
            ],
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "SRT-2026-00001"


@patch("oneerp_selling_app.routes.sales_returns.SalesReturnService")
def test_판매반품_목록_조회(mock_service_cls: MagicMock) -> None:
    """GET /api/v1/sales-returns -- 페이지네이션 응답 구조를 확인한다."""
    service = MagicMock()
    service.list_returns.return_value = {
        "data": [{"_id": "SRT-001", "customer": "CUST-001"}],
        "total": 1,
    }
    mock_service_cls.return_value = service

    response = client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["data"]) == 1


@patch("oneerp_selling_app.routes.sales_returns.SalesReturnService")
def test_판매반품_조회_404(mock_service_cls: MagicMock) -> None:
    """GET /api/v1/sales-returns/{doc_id} -- 없는 문서는 404를 반환한다."""
    service = MagicMock()
    service.get_return.return_value = None
    mock_service_cls.return_value = service

    response = client.get(f"{_BASE_URL}/NONEXISTENT")
    assert response.status_code == 404
