"""E2E: 판매 플로우 — Customer → Quotation → SalesOrder → DeliveryNote → SalesInvoice."""

from __future__ import annotations

import httpx
import pytest

pytestmark = pytest.mark.e2e


class TestSellingFlow:
    """판매 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_고객_CRUD(self, selling_client: httpx.Client) -> None:
        """고객 생성 → 조회 → 수정 → 삭제 플로우."""
        # 생성
        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "E2E 테스트 고객",
                "customer_type": "company",
                "tax_id": "123-45-67890",
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        doc_id = body["_id"]
        assert body["customer_name"] == "E2E 테스트 고객"

        # 목록 조회
        resp = selling_client.get("/api/v1/customers")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

        # 단건 조회
        resp = selling_client.get(f"/api/v1/customers/{doc_id}")
        assert resp.status_code == 200
        assert resp.json()["customer_type"] == "company"

        # 수정
        resp = selling_client.put(
            f"/api/v1/customers/{doc_id}",
            json={
                "customer_name": "E2E 수정 고객",
            },
        )
        assert resp.status_code == 200

        # 삭제
        resp = selling_client.delete(f"/api/v1/customers/{doc_id}")
        assert resp.status_code == 204

        # 삭제 확인
        resp = selling_client.get(f"/api/v1/customers/{doc_id}")
        assert resp.status_code == 404

    def test_견적서_생성_제출_취소(self, selling_client: httpx.Client) -> None:
        """Quotation 생성 → 제출 → 취소 워크플로우."""
        # 고객 생성 (선행 데이터)
        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "견적 테스트 고객",
                "customer_type": "individual",
            },
        )
        assert resp.status_code == 201
        customer_id = resp.json()["_id"]

        # 견적서 생성
        resp = selling_client.post(
            "/api/v1/quotations",
            json={
                "customer_id": customer_id,
                "customer_name": "견적 테스트 고객",
                "transaction_date": "2026-03-17",
                "valid_till": "2026-04-17",
                "items": [
                    {"item_code": "ITEM-001", "item_name": "테스트 품목", "qty": 10, "rate": 1000},
                ],
            },
        )
        assert resp.status_code == 201
        qtn_id = resp.json()["id"]

        # 조회 — 총액 검증
        resp = selling_client.get(f"/api/v1/quotations/{qtn_id}")
        assert resp.status_code == 200
        qtn = resp.json()
        assert qtn["total"] == 10000.0
        assert qtn["docstatus"] == 0  # DRAFT

        # 제출
        resp = selling_client.post(f"/api/v1/quotations/{qtn_id}/submit")
        assert resp.status_code == 200

        # 제출 상태 확인
        resp = selling_client.get(f"/api/v1/quotations/{qtn_id}")
        assert resp.json()["docstatus"] == 1  # SUBMITTED

        # 취소
        resp = selling_client.post(f"/api/v1/quotations/{qtn_id}/cancel")
        assert resp.status_code == 200

        resp = selling_client.get(f"/api/v1/quotations/{qtn_id}")
        assert resp.json()["docstatus"] == 2  # CANCELLED

    def test_판매주문_생성_제출(self, selling_client: httpx.Client) -> None:
        """SalesOrder 생성 → 제출 워크플로우."""
        # 고객 생성
        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "SO 테스트 고객",
                "customer_type": "company",
            },
        )
        customer_id = resp.json()["_id"]

        # 판매주문 생성
        resp = selling_client.post(
            "/api/v1/sales-orders",
            json={
                "customer_id": customer_id,
                "customer_name": "SO 테스트 고객",
                "transaction_date": "2026-03-17",
                "delivery_date": "2026-03-24",
                "items": [
                    {"item_code": "ITEM-A", "item_name": "품목 A", "qty": 5, "rate": 2000},
                    {"item_code": "ITEM-B", "item_name": "품목 B", "qty": 3, "rate": 3000},
                ],
            },
        )
        assert resp.status_code == 201
        so_id = resp.json()["id"]

        # 총액 검증 (5*2000 + 3*3000 = 19000)
        resp = selling_client.get(f"/api/v1/sales-orders/{so_id}")
        assert resp.status_code == 200
        so = resp.json()
        assert so["total"] == 19000.0

        # 제출
        resp = selling_client.post(f"/api/v1/sales-orders/{so_id}/submit")
        assert resp.status_code == 200

    def test_납품서_생성_제출(self, selling_client: httpx.Client) -> None:
        """DeliveryNote 생성 → 제출."""
        # 고객 생성
        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "DN 테스트 고객",
                "customer_type": "individual",
            },
        )
        customer_id = resp.json()["_id"]

        # 납품서 생성
        resp = selling_client.post(
            "/api/v1/delivery-notes",
            json={
                "customer_id": customer_id,
                "customer_name": "DN 테스트 고객",
                "posting_date": "2026-03-17",
                "items": [
                    {"item_code": "ITEM-A", "qty": 5, "warehouse": "메인 창고"},
                ],
            },
        )
        assert resp.status_code == 201
        dn_id = resp.json()["id"]

        # 제출
        resp = selling_client.post(f"/api/v1/delivery-notes/{dn_id}/submit")
        assert resp.status_code == 200

        # 목록 조회
        resp = selling_client.get("/api/v1/delivery-notes")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_판매송장_생성_제출(self, selling_client: httpx.Client) -> None:
        """SalesInvoice 생성 → 제출 + 세금 검증."""
        # 고객 생성
        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "SINV 테스트 고객",
                "customer_type": "company",
            },
        )
        customer_id = resp.json()["_id"]

        # 판매송장 생성
        resp = selling_client.post(
            "/api/v1/sales-invoices",
            json={
                "customer_id": customer_id,
                "customer_name": "SINV 테스트 고객",
                "posting_date": "2026-03-17",
                "due_date": "2026-04-17",
                "items": [
                    {"item_code": "ITEM-A", "item_name": "품목 A", "qty": 10, "rate": 5000},
                ],
                "taxes": [
                    {"tax_type": "부가세", "rate": 10, "amount": 5000},
                ],
            },
        )
        assert resp.status_code == 201
        sinv_id = resp.json()["id"]

        # 조회 — grand_total 검증
        resp = selling_client.get(f"/api/v1/sales-invoices/{sinv_id}")
        assert resp.status_code == 200
        sinv = resp.json()
        assert sinv["grand_total"] == 55000.0  # 50000 + 5000 세금

        # 제출
        resp = selling_client.post(f"/api/v1/sales-invoices/{sinv_id}/submit")
        assert resp.status_code == 200

    def test_견적서_목록_페이지네이션(self, selling_client: httpx.Client) -> None:
        """목록 조회 페이지네이션 파라미터가 동작한다."""
        resp = selling_client.get("/api/v1/quotations", params={"page": 1, "page_size": 5})
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "total" in body
        assert body["page"] == 1
        assert body["page_size"] == 5
