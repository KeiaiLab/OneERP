"""품목(Item) CRUD 엔드포인트 테스트 (OE002 경계 전환 후)."""

from __future__ import annotations

from unittest.mock import MagicMock

import oneerp_stock_app.routes.items as _items_mod
import pytest
from fastapi.testclient import TestClient
from oneerp_stock_app.main import app as stock_app
from oneerp_stock_app.routes.items import get_service

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

TENANT_ADMIN_HEADERS = {
    "X-Tenant-Id": "test-tenant",
    "X-User-Sub": "tenant-admin",
    "X-User-Roles": "admin",
    "X-User-Tier": "tenant_admin",
    "X-User-Permissions": "*:*",
}


def _build_service_mock() -> MagicMock:
    """ItemService 인스턴스를 대체하는 mock. 모든 메서드는 기본 반환값을 가진다."""
    service = MagicMock()
    service.find_existing.return_value = None
    service.get.return_value = None
    service.list.return_value = []
    service.count.return_value = 0
    service.list_variants.return_value = []
    service.list_prices.return_value = []
    service.list_bins.return_value = []
    service.list_ledger.return_value = []
    service.has_variants.return_value = False
    service.has_prices.return_value = False
    service.has_stock_history.return_value = False
    return service


@pytest.fixture
def service_mock():
    """ItemService를 FastAPI DI 오버라이드로 주입한다."""
    mock = _build_service_mock()
    stock_app.dependency_overrides[get_service] = lambda: mock
    try:
        yield mock
    finally:
        stock_app.dependency_overrides.pop(get_service, None)


# --- 생성 ---


def test_품목_생성_정상(service_mock: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    """POST /api/v1/items — 정상 생성 시 201과 item_code를 반환한다."""
    service_mock.find_existing.return_value = None
    service_mock.create.return_value = "ITEM-2026-00001"
    monkeypatch.setattr(
        _items_mod,
        "generate_name",
        lambda prefix, *, tenant_id=None: (
            "ITEM-2026-00001"
            if tenant_id == "test-tenant"
            else (_ for _ in ()).throw(AssertionError("tenant_id 누락"))
        ),
    )

    response = client.post(
        "/api/v1/items",
        json={
            "item_name": "테스트 품목",
            "item_group": "완제품",
        },
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["item_code"] == "ITEM-2026-00001"


# --- 목록 조회 ---


def test_품목_목록_조회(service_mock: MagicMock) -> None:
    """GET /api/v1/items — 페이지네이션 응답 구조를 확인한다."""
    service_mock.list.return_value = [{"_id": "ITEM-2026-00001", "item_name": "테스트"}]
    service_mock.count.return_value = 1

    response = client.get("/api/v1/items?page=1&page_size=10", headers=TENANT_ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    assert len(data["data"]) == 1


def test_품목_목록_그룹_필터(service_mock: MagicMock) -> None:
    """GET /api/v1/items?item_group=완제품 — item_group 필터가 동작한다."""
    service_mock.list.return_value = []
    service_mock.count.return_value = 0

    response = client.get("/api/v1/items?item_group=완제품", headers=TENANT_ADMIN_HEADERS)
    assert response.status_code == 200
    call_args = service_mock.list.call_args
    assert call_args[0][0]["item_group"] == "완제품"


def test_품목_목록은_워크벤치_요약과_상태배지를_반환한다(service_mock: MagicMock) -> None:
    """GET /api/v1/items — 품목 마스터 워크벤치 응답을 반환한다."""
    service_mock.list.return_value = [
        {
            "_id": "ITEM-2026-00001",
            "item_code": "ITEM-2026-00001",
            "item_name": "테스트 품목",
            "item_group": "완제품",
            "reorder_level": 50,
            "is_stock_item": True,
            "has_batch_no": True,
            "has_serial_no": False,
            "default_warehouse": "WH-001",
        }
    ]
    service_mock.count.return_value = 1
    service_mock.list_variants.return_value = [{"_id": "IVR-001", "variant_of": "ITEM-2026-00001"}]
    service_mock.list_prices.return_value = [
        {"_id": "IPR-001", "item_code": "ITEM-2026-00001", "price": 12000.0, "currency": "KRW"},
        {"_id": "IPR-002", "item_code": "ITEM-2026-00001", "price": 14000.0, "currency": "KRW"},
    ]
    service_mock.list_bins.return_value = [
        {
            "_id": "SBIN-001",
            "item_code": "ITEM-2026-00001",
            "warehouse": "WH-001",
            "current_qty": 20,
            "stock_value": 240000.0,
        }
    ]
    service_mock.list_ledger.return_value = [
        {"_id": "SLE-001", "item_code": "ITEM-2026-00001", "posting_date": "2026-04-10"}
    ]

    response = client.get(
        "/api/v1/items?status_badge=reorder_due",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["summary"] == {
        "total_item_count": 1,
        "stock_item_count": 1,
        "service_item_count": 0,
        "reorder_due_count": 1,
        "variant_template_count": 1,
        "tracked_item_count": 1,
    }
    row = payload["data"][0]
    assert row["status_badge"] == "reorder_due"
    assert row["recommended_action"] == "review_replenishment"
    assert row["inventory_summary"] == {
        "warehouse_count": 1,
        "current_qty": 20.0,
        "stock_value": 240000.0,
        "reorder_level": 50.0,
        "is_below_reorder": True,
        "last_movement_date": "2026-04-10",
    }
    assert row["variant_summary"]["variant_count"] == 1
    assert row["pricing_summary"]["price_count"] == 2
    assert row["available_actions"] == [
        "edit",
        "manage_variants",
        "manage_prices",
        "view_stock_balance",
        "open_stock_ledger",
    ]


# --- 단건 조회 ---


def test_품목_단건_조회_정상(service_mock: MagicMock) -> None:
    """GET /api/v1/items/{item_code} — 존재하는 품목을 반환한다."""
    service_mock.get.return_value = {"_id": "ITEM-2026-00001", "item_name": "테스트"}

    response = client.get("/api/v1/items/ITEM-2026-00001", headers=TENANT_ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["item_name"] == "테스트"


def test_품목_단건_조회_미존재(service_mock: MagicMock) -> None:
    """GET /api/v1/items/{item_code} — 없는 품목은 404를 반환한다."""
    service_mock.get.return_value = None

    response = client.get("/api/v1/items/NOT-EXIST", headers=TENANT_ADMIN_HEADERS)
    assert response.status_code == 404


def test_품목_요약은_재고가격변형가이드를_반환한다(service_mock: MagicMock) -> None:
    """GET /api/v1/items/{item_code}/summary — 품목 상세 워크벤치 요약을 반환한다."""
    service_mock.get.return_value = {
        "_id": "ITEM-2026-00001",
        "item_code": "ITEM-2026-00001",
        "item_name": "테스트 품목",
        "item_group": "원자재",
        "reorder_level": 10,
        "is_stock_item": True,
        "has_batch_no": False,
        "has_serial_no": True,
        "default_warehouse": "WH-001",
    }
    service_mock.list_variants.return_value = []
    service_mock.list_prices.return_value = [
        {"_id": "IPR-001", "item_code": "ITEM-2026-00001", "price": 8000.0, "currency": "USD"}
    ]
    service_mock.list_bins.return_value = [
        {
            "_id": "SBIN-001",
            "item_code": "ITEM-2026-00001",
            "warehouse": "WH-001",
            "current_qty": 30,
            "stock_value": 240000.0,
        }
    ]
    service_mock.list_ledger.return_value = [
        {"_id": "SLE-001", "item_code": "ITEM-2026-00001", "posting_date": "2026-04-09"}
    ]

    response = client.get(
        "/api/v1/items/ITEM-2026-00001/summary",
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["status_badge"] == "tracking_required"
    assert payload["recommended_action"] == "verify_tracking_policy"
    assert payload["variant_summary"]["variant_count"] == 0
    assert payload["pricing_summary"] == {
        "price_count": 1,
        "price_list_count": 1,
        "min_price": 8000.0,
        "max_price": 8000.0,
        "currency": "USD",
    }
    assert payload["available_actions"] == [
        "edit",
        "manage_variants",
        "manage_prices",
        "view_stock_balance",
        "open_stock_ledger",
    ]


# --- 수정 ---


def test_품목_수정_정상(service_mock: MagicMock) -> None:
    """PUT /api/v1/items/{item_code} — 정상 수정 시 200을 반환한다."""
    service_mock.get.return_value = {"_id": "ITEM-2026-00001", "item_name": "테스트"}

    response = client.put(
        "/api/v1/items/ITEM-2026-00001",
        json={"item_name": "수정된 품목"},
        headers=TENANT_ADMIN_HEADERS,
    )
    assert response.status_code == 200
    assert response.json()["message"] == "품목이 수정되었습니다"
    service_mock.update.assert_called_once()


# --- 삭제 ---


def test_품목_삭제_정상(service_mock: MagicMock) -> None:
    """DELETE /api/v1/items/{item_code} — 초안 상태 품목을 삭제한다."""
    service_mock.get.return_value = {"_id": "ITEM-2026-00001", "docstatus": 0}
    service_mock.has_variants.return_value = False
    service_mock.has_prices.return_value = False
    service_mock.has_stock_history.return_value = False

    response = client.delete("/api/v1/items/ITEM-2026-00001", headers=TENANT_ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["message"] == "품목이 삭제되었습니다"
    service_mock.delete.assert_called_once_with("ITEM-2026-00001")


def test_품목_삭제_미존재(service_mock: MagicMock) -> None:
    """DELETE /api/v1/items/{item_code} — 없는 품목 삭제 시 404를 반환한다."""
    service_mock.get.return_value = None

    response = client.delete("/api/v1/items/NOT-EXIST", headers=TENANT_ADMIN_HEADERS)
    assert response.status_code == 404


def test_품목_삭제는_연결된_변형이나_재고이력이_있으면_차단된다(
    service_mock: MagicMock,
) -> None:
    """DELETE /api/v1/items/{item_code} — 연결 데이터가 있으면 삭제를 차단한다."""
    service_mock.get.return_value = {"_id": "ITEM-2026-00001", "docstatus": 0}
    service_mock.has_variants.return_value = True
    service_mock.has_prices.return_value = False
    service_mock.has_stock_history.return_value = True

    response = client.delete("/api/v1/items/ITEM-2026-00001", headers=TENANT_ADMIN_HEADERS)
    assert response.status_code == 422
    assert response.json()["error"] == "품목 변형·가격·재고 이력이 연결된 품목은 삭제할 수 없습니다"
    assert response.json()["detail"] == "ERR-STK-033"
    service_mock.delete.assert_not_called()
