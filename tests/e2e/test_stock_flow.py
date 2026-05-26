"""E2E: 재고 플로우 — Item → Warehouse → StockEntry → Batch."""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.conftest import wait_for_condition

pytestmark = pytest.mark.e2e


class TestStockFlow:
    """재고 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_품목_CRUD(self, stock_client: httpx.Client) -> None:
        """품목 생성 → 조회 → 수정 → 삭제."""
        resp = stock_client.post(
            "/api/v1/items",
            json={
                "item_name": "E2E 테스트 품목",
                "item_group": "원자재",
                "stock_uom": "EA",
                "is_stock_item": True,
            },
        )
        assert resp.status_code == 201
        item_code = resp.json()["item_code"]

        # 조회
        resp = stock_client.get(f"/api/v1/items/{item_code}")
        assert resp.status_code == 200
        item = resp.json()
        assert item["item_name"] == "E2E 테스트 품목"
        assert item["valuation_method"] == "FIFO"

        # 목록
        resp = stock_client.get("/api/v1/items")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        # 수정
        resp = stock_client.put(
            f"/api/v1/items/{item_code}",
            json={
                "item_name": "E2E 수정 품목",
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = stock_client.delete(f"/api/v1/items/{item_code}")
        assert resp.status_code == 200

    def test_창고_CRUD(self, stock_client: httpx.Client) -> None:
        """창고 생성 → 조회 → 수정 → 삭제."""
        resp = stock_client.post(
            "/api/v1/warehouses/",
            json={
                "warehouse_name": "E2E 메인 창고",
                "warehouse_type": "stores",
                "company": "E2E 회사",
            },
        )
        assert resp.status_code == 201
        wh_id = resp.json()["warehouse_id"]

        # 조회
        resp = stock_client.get(f"/api/v1/warehouses/{wh_id}")
        assert resp.status_code == 200
        assert resp.json()["warehouse_name"] == "E2E 메인 창고"

        # 수정
        resp = stock_client.put(
            f"/api/v1/warehouses/{wh_id}",
            json={
                "warehouse_name": "E2E 수정 창고",
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = stock_client.delete(f"/api/v1/warehouses/{wh_id}")
        assert resp.status_code == 200

    def test_재고입고_생성(self, stock_client: httpx.Client) -> None:
        """StockEntry(receipt) 생성 → 조회."""
        resp = stock_client.post(
            "/api/v1/stock-entries",
            json={
                "entry_type": "receipt",
                "posting_date": "2026-03-17",
                "items": [
                    {
                        "item_code": "ITEM-E2E",
                        "item_name": "입고 품목",
                        "qty": 100,
                        "target_warehouse": "메인 창고",
                        "valuation_rate": 1000,
                    },
                ],
                "remarks": "E2E 테스트 입고",
            },
        )
        assert resp.status_code == 201
        entry_id = resp.json()["entry_id"]

        # 조회
        resp = stock_client.get(f"/api/v1/stock-entries/{entry_id}")
        assert resp.status_code == 200
        entry = resp.json()
        assert entry["entry_type"] == "receipt"
        assert len(entry["items"]) == 1

    def test_재고출고_생성(self, stock_client: httpx.Client) -> None:
        """StockEntry(issue) 생성 → 조회."""
        resp = stock_client.post(
            "/api/v1/stock-entries",
            json={
                "entry_type": "issue",
                "posting_date": "2026-03-17",
                "items": [
                    {
                        "item_code": "ITEM-E2E",
                        "item_name": "출고 품목",
                        "qty": 10,
                        "source_warehouse": "메인 창고",
                        "valuation_rate": 1000,
                    },
                ],
            },
        )
        assert resp.status_code == 201

    def test_재고이동_생성(self, stock_client: httpx.Client) -> None:
        """StockEntry(transfer) 생성 → 조회."""
        resp = stock_client.post(
            "/api/v1/stock-entries",
            json={
                "entry_type": "transfer",
                "posting_date": "2026-03-17",
                "items": [
                    {
                        "item_code": "ITEM-E2E",
                        "item_name": "이동 품목",
                        "qty": 5,
                        "source_warehouse": "메인 창고",
                        "target_warehouse": "보조 창고",
                        "valuation_rate": 1000,
                    },
                ],
            },
        )
        assert resp.status_code == 201

    def test_배치_생성_조회(self, stock_client: httpx.Client) -> None:
        """Batch 생성 → 조회."""
        resp = stock_client.post(
            "/api/v1/batches/",
            json={
                "item_code": "ITEM-BATCH",
                "manufacturing_date": "2026-03-01",
                "expiry_date": "2027-03-01",
            },
        )
        assert resp.status_code == 201
        batch_id = resp.json()["batch_id"]

        resp = stock_client.get(f"/api/v1/batches/{batch_id}")
        assert resp.status_code == 200
        assert resp.json()["item_code"] == "ITEM-BATCH"

    def test_재고전표_목록_필터(self, stock_client: httpx.Client) -> None:
        """StockEntry 목록 조회 + entry_type 필터."""
        resp = stock_client.get(
            "/api/v1/stock-entries",
            params={"entry_type": "receipt"},
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_품목_워크벤치는_재고가격변형요약과_삭제가이드를_반환한다(
        self, stock_client: httpx.Client
    ) -> None:
        """품목 워크벤치가 재고·가격·변형 요약과 삭제 가이드를 제공한다."""
        item_code = "ITEM-WORKBENCH-E2E"
        headers = {
            "X-Tenant-Id": "oneerp_e2e_test",
            "X-User-Sub": "e2e-user",
            "X-User-Roles": "admin",
            "X-User-Permissions": "*:*",
            "X-User-Tier": "super_admin",
        }
        resp = stock_client.post(
            "/api/v1/items",
            json={
                "item_code": item_code,
                "item_name": "워크벤치 품목",
                "item_group": "원자재",
                "stock_uom": "EA",
                "is_stock_item": True,
                "reorder_level": 50,
                "has_batch_no": True,
            },
            headers=headers,
        )
        assert resp.status_code == 201

        resp = stock_client.post(
            "/api/v1/item-variants",
            json={
                "item_code": f"{item_code}-RED",
                "variant_of": item_code,
                "attributes": {"color": "red"},
            },
            headers=headers,
        )
        assert resp.status_code == 201

        resp = stock_client.post(
            "/api/v1/item-prices",
            json={
                "item_code": item_code,
                "price_list": "표준구매가",
                "price": 12500.0,
                "currency": "KRW",
                "min_qty": 1,
            },
            headers=headers,
        )
        assert resp.status_code == 201

        resp = stock_client.post(
            "/api/v1/stock-entries",
            json={
                "entry_type": "receipt",
                "posting_date": "2026-04-10",
                "items": [
                    {
                        "item_code": item_code,
                        "item_name": "워크벤치 품목",
                        "qty": 20,
                        "target_warehouse": "메인 창고",
                        "valuation_rate": 12500,
                    }
                ],
            },
            headers=headers,
        )
        assert resp.status_code == 201
        entry_id = resp.json()["entry_id"]

        resp = stock_client.post(
            f"/api/v1/stock-entries/{entry_id}/submit",
            headers=headers,
        )
        assert resp.status_code == 200

        def stock_is_reflected() -> dict | None:
            resp = stock_client.get(f"/api/v1/items/{item_code}/summary", headers=headers)
            if resp.status_code != 200:
                return None
            body = resp.json()
            if body["inventory_summary"]["current_qty"] == 20.0:
                return body
            return None

        detail = wait_for_condition(
            stock_is_reflected,
            timeout=12.0,
            interval=0.5,
            description="재고이동 제출 후 품목 현재고 반영",
        )

        resp = stock_client.get(
            "/api/v1/items",
            params={"item_group": "원자재", "status_badge": "reorder_due"},
            headers=headers,
        )
        assert resp.status_code == 200
        payload = resp.json()
        row = next(item for item in payload["data"] if item["item_code"] == item_code)
        assert payload["summary"]["reorder_due_count"] >= 1
        assert row["status_badge"] == "reorder_due"
        assert row["recommended_action"] == "review_replenishment"
        assert row["variant_summary"]["variant_count"] == 1
        assert row["pricing_summary"]["price_count"] == 1
        assert row["inventory_summary"]["is_below_reorder"] is True

        assert detail["inventory_summary"]["current_qty"] == 20.0
        assert detail["pricing_summary"]["max_price"] == 12500.0
        assert detail["available_actions"] == [
            "edit",
            "manage_variants",
            "manage_prices",
            "view_stock_balance",
            "open_stock_ledger",
        ]

        resp = stock_client.delete(f"/api/v1/items/{item_code}", headers=headers)
        assert resp.status_code == 422
        assert resp.json()["error"] == "품목 변형·가격·재고 이력이 연결된 품목은 삭제할 수 없습니다"
        assert resp.json()["detail"] == "ERR-STK-033"
