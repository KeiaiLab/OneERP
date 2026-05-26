"""구매반품(PurchaseReturn) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from oneerp_buying_app.main import app

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


_BASE_URL = "/api/v1/purchase-returns"


@patch("oneerp_buying_app.routes.purchase_returns._get_repo")
@patch("oneerp_buying_app.routes.purchase_returns.generate_name", return_value="PRT-2026-00001")
def test_구매반품_생성_정상(mock_name: MagicMock, mock_repo: MagicMock) -> None:
    """POST /api/v1/purchase-returns -- 정상 생성 시 201을 반환한다."""
    mock_repo.return_value = MagicMock()
    response = client.post(
        _BASE_URL,
        json={
            "supplier": "SUP-001",
            "return_date": "2026-03-18",
            "reason": "불량품",
            "items": [
                {"item_code": "ITEM-001", "item_name": "원자재A", "qty": 5, "rate": 3000},
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == "PRT-2026-00001"


@patch("oneerp_buying_app.routes.purchase_returns._get_repo")
def test_구매반품_목록_조회(mock_repo: MagicMock) -> None:
    """GET /api/v1/purchase-returns -- 페이지네이션 응답 구조를 확인한다."""
    repo = MagicMock()
    repo.find_many.return_value = [{"_id": "PRT-001", "supplier": "업체A"}]
    repo.count.return_value = 1
    mock_repo.return_value = repo
    response = client.get(f"{_BASE_URL}?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["data"]) == 1


@patch("oneerp_buying_app.routes.purchase_returns._get_repo")
def test_구매반품_조회_404(mock_repo: MagicMock) -> None:
    """GET /api/v1/purchase-returns/{doc_id} -- 없는 구매반품은 404를 반환한다."""
    repo = MagicMock()
    repo.find_by_id.return_value = None
    mock_repo.return_value = repo
    response = client.get(f"{_BASE_URL}/NOT-EXIST")
    assert response.status_code == 404
