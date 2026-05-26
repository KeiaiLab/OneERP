"""재고잔액(StockBalance) 리포트 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_stock_app.routes.stock_balances as _mod
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


def _mock_repo() -> MagicMock:
    """공통 Repository mock을 반환한다."""
    return MagicMock()


def test_재고잔액_목록_조회(monkeypatch: object) -> None:
    """GET /api/v1/stock-balances — 페이지네이션 응답 구조를 확인한다."""
    repo = _mock_repo()
    repo.find_many.return_value = [{"_id": "SBAL-001", "item_code": "ITEM-001", "actual_qty": 100}]
    repo.count.return_value = 1
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/stock-balances?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["data"]) == 1


def test_재고잔액_품목코드_필터(monkeypatch: object) -> None:
    """GET /api/v1/stock-balances?item_code=ITEM-001 — 품목코드 필터가 동작한다."""
    repo = _mock_repo()
    repo.find_many.return_value = []
    repo.count.return_value = 0
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/stock-balances?item_code=ITEM-001")
    assert response.status_code == 200
    call_args = repo.find_many.call_args
    assert call_args[0][0]["item_code"] == "ITEM-001"


def test_재고잔액_창고_필터(monkeypatch: object) -> None:
    """GET /api/v1/stock-balances?warehouse=WH-001 — 창고 필터가 동작한다."""
    repo = _mock_repo()
    repo.find_many.return_value = []
    repo.count.return_value = 0
    monkeypatch.setattr(_mod, "_get_repo", lambda: repo)  # type: ignore[attr-defined]

    response = client.get("/api/v1/stock-balances?warehouse=WH-001")
    assert response.status_code == 200
    call_args = repo.find_many.call_args
    assert call_args[0][0]["warehouse"] == "WH-001"
