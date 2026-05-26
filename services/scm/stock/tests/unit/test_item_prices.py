"""품목가격(ItemPrice) CRUD 엔드포인트 테스트."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_stock_app.routes.item_prices as _mod
import pytest
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


def test_품목가격_생성_정상(monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/v1/item-prices — 정상 생성 시 201을 반환한다."""
    repo = _mock_repo()
    monkeypatch.setattr(
        _mod,
        "_get_repo",
        lambda tenant_id="": (
            repo
            if tenant_id == "test-tenant"
            else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
        ),
    )
    monkeypatch.setattr(_mod, "generate_name", lambda prefix, **_: "IPR-2026-00001")

    response = client.post(
        "/api/v1/item-prices",
        json={
            "item_code": "ITEM-001",
            "price_list": "표준판매가",
            "price": 15000.0,
            "currency": "KRW",
            "min_qty": 1.0,
        },
    )
    assert response.status_code == 201
    assert response.json()["id"] == "IPR-2026-00001"


def test_품목가격_목록_조회(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/v1/item-prices — 페이지네이션 응답 구조를 확인한다."""
    repo = _mock_repo()
    repo.find_many.return_value = [{"_id": "IPR-001"}]
    repo.count.return_value = 1
    monkeypatch.setattr(
        _mod,
        "_get_repo",
        lambda tenant_id="": (
            repo
            if tenant_id == "test-tenant"
            else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
        ),
    )

    response = client.get("/api/v1/item-prices?page=1&page_size=10")
    assert response.status_code == 200
    assert response.json()["total"] == 1


def test_품목가격_조회_미존재_404(monkeypatch: pytest.MonkeyPatch) -> None:
    """GET /api/v1/item-prices/{doc_id} — 없는 품목가격은 404를 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = None
    monkeypatch.setattr(
        _mod,
        "_get_repo",
        lambda tenant_id="": (
            repo
            if tenant_id == "test-tenant"
            else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
        ),
    )

    response = client.get("/api/v1/item-prices/NOT-EXIST")
    assert response.status_code == 404


def test_품목가격_수정_정상(monkeypatch: pytest.MonkeyPatch) -> None:
    """PUT /api/v1/item-prices/{doc_id} — 정상 수정 시 200을 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "IPR-001"}
    monkeypatch.setattr(
        _mod,
        "_get_repo",
        lambda tenant_id="": (
            repo
            if tenant_id == "test-tenant"
            else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
        ),
    )

    response = client.put(
        "/api/v1/item-prices/IPR-001",
        json={"price": 20000.0},
    )
    assert response.status_code == 200


def test_품목가격_삭제_정상(monkeypatch: pytest.MonkeyPatch) -> None:
    """DELETE /api/v1/item-prices/{doc_id} — 정상 삭제 시 204를 반환한다."""
    repo = _mock_repo()
    repo.find_by_id.return_value = {"_id": "IPR-001"}
    monkeypatch.setattr(
        _mod,
        "_get_repo",
        lambda tenant_id="": (
            repo
            if tenant_id == "test-tenant"
            else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
        ),
    )

    response = client.delete("/api/v1/item-prices/IPR-001")
    assert response.status_code == 204
