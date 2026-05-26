"""E2E: FL5 생산 플로우 — BOM → 원자재 재고 → 생산계획 → MRP → 작업지시 → 완료 → 재고이동 → 원가분개.

제조(manufacturing), 재고(stock), 회계(accounting) 서비스 간 전체 경로를 검증한다.
"""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e


class TestManufacturingFlow:
    """FL5 Manufacture-to-Stock 전체 시나리오를 검증한다."""

    # ------------------------------------------------------------------
    # 1. BOM CRUD 기본 검증
    # ------------------------------------------------------------------
    def test_BOM_CRUD(self, manufacturing_client: httpx.Client) -> None:
        """BOM 생성 → 조회 → 수정 → 삭제."""
        resp = manufacturing_client.post(
            "/api/v1/boms",
            json={
                "item_code": "FG-001",
                "item_name": "완제품 A",
                "quantity": 1.0,
                "items": [
                    {"item_code": "RM-001", "item_name": "원자재 1", "qty": 2, "rate": 500},
                    {"item_code": "RM-002", "item_name": "원자재 2", "qty": 1, "rate": 300},
                ],
                "is_default": True,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        bom_id = resp.json()["id"]

        # 조회
        resp = manufacturing_client.get(f"/api/v1/boms/{bom_id}", headers=HEADERS)
        assert resp.status_code == 200
        bom = resp.json()
        assert bom["item_code"] == "FG-001"
        assert len(bom["items"]) == 2

        # 수정
        resp = manufacturing_client.put(
            f"/api/v1/boms/{bom_id}",
            json={
                "quantity": 10.0,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # 목록
        resp = manufacturing_client.get("/api/v1/boms", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        # 삭제
        resp = manufacturing_client.delete(f"/api/v1/boms/{bom_id}", headers=HEADERS)
        assert resp.status_code == 204

    # ------------------------------------------------------------------
    # 2. 작업지시 생성 → 제출 → 취소 기본 워크플로우
    # ------------------------------------------------------------------
    def test_작업지시_생성_제출_취소(self, manufacturing_client: httpx.Client) -> None:
        """WorkOrder 생성 → 제출 → 취소 워크플로우."""
        # BOM 생성 (선행 데이터)
        resp = manufacturing_client.post(
            "/api/v1/boms",
            json={
                "item_code": "FG-WO",
                "item_name": "작업지시 완제품",
                "quantity": 1.0,
                "items": [
                    {"item_code": "RM-WO-1", "item_name": "자재 1", "qty": 3, "rate": 100},
                ],
            },
            headers=HEADERS,
        )
        bom_id = resp.json()["id"]

        # 작업지시 생성
        resp = manufacturing_client.post(
            "/api/v1/work-orders",
            json={
                "production_item": "FG-WO",
                "bom_ref": bom_id,
                "qty": 50,
                "planned_start_date": "2026-03-20",
                "planned_end_date": "2026-03-25",
                "warehouse": "생산 창고",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        wo_id = resp.json()["id"]

        # 조회
        resp = manufacturing_client.get(f"/api/v1/work-orders/{wo_id}", headers=HEADERS)
        assert resp.status_code == 200
        wo = resp.json()
        assert wo["qty"] == 50
        assert wo["docstatus"] == 0

        # 제출
        resp = manufacturing_client.post(f"/api/v1/work-orders/{wo_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        # 취소
        resp = manufacturing_client.post(f"/api/v1/work-orders/{wo_id}/cancel", headers=HEADERS)
        assert resp.status_code == 200

        resp = manufacturing_client.get(f"/api/v1/work-orders/{wo_id}", headers=HEADERS)
        assert resp.json()["docstatus"] == 2

    # ------------------------------------------------------------------
    # 3. 생산계획 생성 → 제출 워크플로우
    # ------------------------------------------------------------------
    def test_생산계획_생성_제출(self, manufacturing_client: httpx.Client) -> None:
        """생산계획 생성 → 제출 워크플로우."""
        resp = manufacturing_client.post(
            "/api/v1/production-plans",
            json={
                "planned_start": "2026-04-01",
                "planned_end": "2026-04-30",
                "status": "draft",
                "items": [
                    {"item_code": "FG-PP-001", "qty": 100, "warehouse": "생산 창고"},
                    {"item_code": "FG-PP-002", "qty": 200, "warehouse": "생산 창고"},
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        pp_id = resp.json()["id"]

        # 조회
        resp = manufacturing_client.get(f"/api/v1/production-plans/{pp_id}", headers=HEADERS)
        assert resp.status_code == 200
        pp = resp.json()
        assert len(pp.get("items", [])) == 2

        # 제출
        resp = manufacturing_client.post(
            f"/api/v1/production-plans/{pp_id}/submit", headers=HEADERS
        )
        assert resp.status_code == 200

        # 제출 후 상태 확인
        resp = manufacturing_client.get(f"/api/v1/production-plans/{pp_id}", headers=HEADERS)
        assert resp.json().get("docstatus") == 1

    # ------------------------------------------------------------------
    # 4. 재고이동(Stock Entry) — 자재 출고 + 완제품 입고
    # ------------------------------------------------------------------
    def test_재고이동_자재출고_완제품입고(self, stock_client: httpx.Client) -> None:
        """자재출고(material_issue) + 완제품입고(manufacture) StockEntry 생성 → 제출."""
        # 4-a. 자재 출고(원자재 차감)
        resp = stock_client.post(
            "/api/v1/stock-entries",
            json={
                "entry_type": "material_issue",
                "posting_date": "2026-03-27",
                "items": [
                    {
                        "item_code": "RM-SE-001",
                        "qty": 10,
                        "warehouse": "원자재 창고",
                        "rate": 500,
                    },
                ],
                "reference_type": "WorkOrder",
                "reference_id": "WO-DUMMY-001",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        issue_id = resp.json()["entry_id"]

        # 제출
        resp = stock_client.post(f"/api/v1/stock-entries/{issue_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        # 4-b. 완제품 입고
        resp = stock_client.post(
            "/api/v1/stock-entries",
            json={
                "entry_type": "manufacture",
                "posting_date": "2026-03-27",
                "items": [
                    {
                        "item_code": "FG-SE-001",
                        "qty": 5,
                        "warehouse": "완제품 창고",
                        "rate": 1300,
                    },
                ],
                "reference_type": "WorkOrder",
                "reference_id": "WO-DUMMY-001",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        receipt_id = resp.json()["entry_id"]

        # 제출
        resp = stock_client.post(f"/api/v1/stock-entries/{receipt_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        # 재고이동 목록 확인 — entry_type 필터
        resp = stock_client.get(
            "/api/v1/stock-entries",
            params={"entry_type": "manufacture"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    # ------------------------------------------------------------------
    # 5. 원가 분개(Journal Entry) — 자재비·가공비 분개 생성
    # ------------------------------------------------------------------
    def test_원가분개_생성_제출(self, accounting_client: httpx.Client) -> None:
        """생산원가 분개전표 생성 → 제출 (차변: 재공품, 대변: 원자재)."""
        resp = accounting_client.post(
            "/api/v1/journal-entries",
            json={
                "posting_date": "2026-03-27",
                "voucher_type": "manufacturing_cost",
                "remark": "작업지시 WO-TEST 원가 분개",
                "items": [
                    {
                        "account": "재공품",
                        "debit": 5000,
                        "credit": 0,
                        "cost_center": "생산부",
                    },
                    {
                        "account": "원자재",
                        "debit": 0,
                        "credit": 5000,
                        "cost_center": "생산부",
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        je = resp.json()
        je_id = je["_id"]
        # 차대변 일치 확인
        assert je["total_debit"] == je["total_credit"] == 5000

        # 제출
        resp = accounting_client.post(f"/api/v1/journal-entries/{je_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

    # ------------------------------------------------------------------
    # 6. 작업카드 워크플로우
    # ------------------------------------------------------------------
    def test_작업카드_생성_제출(self, manufacturing_client: httpx.Client) -> None:
        """작업카드 생성 → 제출 → 취소."""
        resp = manufacturing_client.post(
            "/api/v1/job-cards",
            json={
                "work_order": "WO-JC-TEST",
                "operation": "절단",
                "workstation": "절단기-A",
                "employee_id": "EMP-001",
                "status": "draft",
                "planned_time": 120.0,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        jc_id = resp.json()["id"]

        # 조회
        resp = manufacturing_client.get(f"/api/v1/job-cards/{jc_id}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["operation"] == "절단"

        # 제출
        resp = manufacturing_client.post(f"/api/v1/job-cards/{jc_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        # 취소
        resp = manufacturing_client.post(f"/api/v1/job-cards/{jc_id}/cancel", headers=HEADERS)
        assert resp.status_code == 200

    # ------------------------------------------------------------------
    # 7. BOM 트리 조회
    # ------------------------------------------------------------------
    def test_BOM_트리_조회(self, manufacturing_client: httpx.Client) -> None:
        """BOM 트리(1단계 전개) 조회."""
        # BOM 생성
        resp = manufacturing_client.post(
            "/api/v1/boms",
            json={
                "item_code": "FG-TREE",
                "item_name": "트리 완제품",
                "quantity": 1.0,
                "items": [
                    {"item_code": "RM-T-1", "item_name": "부품 1", "qty": 2, "rate": 100},
                    {"item_code": "RM-T-2", "item_name": "부품 2", "qty": 3, "rate": 200},
                ],
            },
            headers=HEADERS,
        )
        bom_id = resp.json()["id"]

        resp = manufacturing_client.get(f"/api/v1/boms/{bom_id}/tree", headers=HEADERS)
        assert resp.status_code == 200
        tree = resp.json()
        assert len(tree["children"]) == 2

    # ------------------------------------------------------------------
    # 8. 재고잔액 리포트 조회
    # ------------------------------------------------------------------
    def test_재고잔액_리포트(self, stock_client: httpx.Client) -> None:
        """재고잔액 리포트가 정상 응답한다."""
        resp = stock_client.get("/api/v1/stock-balances", headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "total" in body

    # ------------------------------------------------------------------
    # 9. 생산원가 리포트 조회
    # ------------------------------------------------------------------
    def test_생산원가_리포트(self, manufacturing_client: httpx.Client) -> None:
        """생산원가 리포트가 정상 응답한다."""
        resp = manufacturing_client.get("/api/v1/production-costs", headers=HEADERS)
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "total" in body
