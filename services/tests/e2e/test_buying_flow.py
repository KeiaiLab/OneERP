"""E2E: 구매 플로우 — Supplier → PurchaseOrder → PurchaseInvoice."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.e2e


class TestBuyingFlow:
    """구매 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_공급업체_CRUD(self, buying_client: httpx.Client) -> None:
        """공급업체 생성 → 조회 → 수정 → 삭제."""
        resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "E2E 공급업체",
                "supplier_type": "company",
                "tax_id": "987-65-43210",
                "payment_terms": "30일",
            },
        )
        assert resp.status_code == 201
        doc_id = resp.json()["_id"]

        # 목록
        resp = buying_client.get("/api/v1/suppliers")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

        # 단건 조회
        resp = buying_client.get(f"/api/v1/suppliers/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["supplier_name"] == "E2E 공급업체"

        # 수정
        resp = buying_client.put(
            f"/api/v1/suppliers/{doc_id}",
            json={
                "supplier_name": "E2E 수정 공급업체",
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = buying_client.delete(f"/api/v1/suppliers/{doc_id}")
        assert resp.status_code == 204

    def test_구매주문_생성_제출_취소(self, buying_client: httpx.Client) -> None:
        """PurchaseOrder 생성 → 제출 → 취소 워크플로우."""
        # 공급업체 생성
        resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "PO 테스트 공급업체",
                "supplier_type": "individual",
            },
        )
        supplier_id = resp.json()["_id"]

        # 구매주문 생성
        resp = buying_client.post(
            "/api/v1/purchase-orders",
            json={
                "supplier_id": supplier_id,
                "supplier_name": "PO 테스트 공급업체",
                "transaction_date": "2026-03-17",
                "items": [
                    {"item_code": "RAW-001", "item_name": "원자재 A", "qty": 100, "rate": 500},
                ],
            },
        )
        assert resp.status_code == 201
        po_id = resp.json()["id"]

        # 조회 — 총액 검증
        resp = buying_client.get(f"/api/v1/purchase-orders/{po_id}")
        assert resp.status_code == 200
        po = resp.json()
        assert po["total"] == 50000.0
        assert po["docstatus"] == 0

        # 제출
        resp = buying_client.post(f"/api/v1/purchase-orders/{po_id}/submit")
        assert resp.status_code == 200

        # 취소
        resp = buying_client.post(f"/api/v1/purchase-orders/{po_id}/cancel")
        assert resp.status_code == 200

        resp = buying_client.get(f"/api/v1/purchase-orders/{po_id}")
        assert resp.json()["docstatus"] == 2

    def test_구매송장_생성_제출(self, buying_client: httpx.Client) -> None:
        """PurchaseInvoice 생성 → 제출."""
        # 공급업체 생성
        resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "PI 테스트 공급업체",
                "supplier_type": "company",
            },
        )
        supplier_id = resp.json()["_id"]

        # 구매송장 생성
        resp = buying_client.post(
            "/api/v1/purchase-invoices",
            json={
                "supplier_id": supplier_id,
                "supplier_name": "PI 테스트 공급업체",
                "posting_date": "2026-03-17",
                "due_date": "2026-04-17",
                "items": [
                    {"item_code": "RAW-001", "item_name": "원자재 A", "qty": 50, "rate": 500},
                ],
                "taxes": [
                    {"tax_type": "부가세", "rate": 10, "amount": 2500},
                ],
            },
        )
        assert resp.status_code == 201
        pi_id = resp.json()["id"]

        # 조회
        resp = buying_client.get(f"/api/v1/purchase-invoices/{pi_id}")
        assert resp.status_code == 200
        pi = resp.json()
        assert pi["grand_total"] == 27500.0  # 25000 + 2500

        # 제출
        resp = buying_client.post(f"/api/v1/purchase-invoices/{pi_id}/submit")
        assert resp.status_code == 200

    def test_구매주문_목록_페이지네이션(self, buying_client: httpx.Client) -> None:
        """목록 조회 페이지네이션 동작 검증."""
        resp = buying_client.get("/api/v1/purchase-orders", params={"page": 1, "page_size": 5})
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "total" in body
