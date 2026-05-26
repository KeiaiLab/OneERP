"""E2E: 구매 플로우 — Supplier → PurchaseOrder → PurchaseInvoice."""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.conftest import wait_for_condition
from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e


def _document_id(payload: dict[str, object]) -> str:
    """문서 응답에서 공개 id 또는 내부 _id를 추출한다."""
    value = payload.get("id") or payload.get("_id")
    assert isinstance(value, str)
    return value


class TestBuyingFlow:
    """구매 모듈의 전체 사용자 시나리오를 검증한다."""

    def test_자재요청에서_직접_RFQ를_생성한다(self, buying_client: httpx.Client) -> None:
        """구매 자재요청에서 바로 RFQ를 생성해 공급업체 비교 흐름으로 넘긴다."""
        supplier_a_resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "MR RFQ 공급업체 A",
                "supplier_type": "company",
            },
            headers=HEADERS,
        )
        assert supplier_a_resp.status_code == 201
        supplier_a_id = supplier_a_resp.json()["_id"]

        supplier_b_resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "MR RFQ 공급업체 B",
                "supplier_type": "company",
            },
            headers=HEADERS,
        )
        assert supplier_b_resp.status_code == 201
        supplier_b_id = supplier_b_resp.json()["_id"]

        mr_resp = buying_client.post(
            "/api/v1/material-requests",
            json={
                "request_type": "purchase",
                "required_date": "2026-04-10",
                "budget_limit": 500000,
                "items": [
                    {
                        "item_code": "MR-RFQ-001",
                        "item_name": "MR에서 RFQ로 보낼 원자재",
                        "item_group": "원자재",
                        "qty": 5,
                        "warehouse": "WH-001",
                        "estimated_unit_cost": 50000,
                    }
                ],
            },
            headers=HEADERS,
        )
        assert mr_resp.status_code == 201
        mr_id = mr_resp.json()["id"]

        create_rfq_resp = buying_client.post(
            f"/api/v1/material-requests/{mr_id}/create-rfq",
            json={
                "suppliers": [supplier_a_id, supplier_b_id],
                "transaction_date": "2026-04-09",
            },
            headers=HEADERS,
        )
        assert create_rfq_resp.status_code == 201
        rfq_id = create_rfq_resp.json()["id"]
        assert create_rfq_resp.json()["material_request_id"] == mr_id

        rfq_resp = buying_client.get(
            f"/api/v1/request-for-quotations/{rfq_id}",
            headers=HEADERS,
        )
        assert rfq_resp.status_code == 200
        rfq_doc = rfq_resp.json()
        assert rfq_doc["material_request"] == mr_id
        assert rfq_doc["suppliers"] == [supplier_a_id, supplier_b_id]
        assert rfq_doc["items"][0]["item_code"] == "MR-RFQ-001"
        assert rfq_doc["items"][0]["qty"] == 5

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

    def test_공급업체_워크벤치는_거래요약과_삭제차단을_보여준다(
        self,
        buying_client: httpx.Client,
    ) -> None:
        """공급업체 목록/상세/요약은 거래 워크벤치 정보를 제공하고 거래 이력 삭제를 막는다."""
        resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "워크벤치 공급업체",
                "supplier_group": "원자재",
                "supplier_type": "company",
                "payment_terms": "30일",
                "supplied_items": ["ITEM-SUP-001"],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        supplier_id = _document_id(resp.json())

        resp = buying_client.post(
            "/api/v1/purchase-orders",
            json={
                "supplier_id": supplier_id,
                "supplier_name": "워크벤치 공급업체",
                "transaction_date": "2026-04-10",
                "items": [
                    {
                        "item_code": "ITEM-SUP-001",
                        "item_name": "원자재A",
                        "qty": 10,
                        "rate": 14000,
                    }
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        po_id = _document_id(resp.json())

        resp = buying_client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = buying_client.post(
            "/api/v1/purchase-invoices",
            json={
                "supplier_id": supplier_id,
                "supplier_name": "워크벤치 공급업체",
                "posting_date": "2026-04-10",
                "due_date": "2026-05-10",
                "items": [
                    {
                        "item_code": "ITEM-SUP-001",
                        "item_name": "원자재A",
                        "qty": 10,
                        "rate": 14000,
                    }
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        invoice_id = _document_id(resp.json())

        resp = buying_client.post(
            f"/api/v1/purchase-invoices/{invoice_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = buying_client.post(
            "/api/v1/supplier-scorecards",
            json={
                "supplier": supplier_id,
                "evaluation_period": "2026-04",
                "total_score": 72.5,
                "criteria": {"delivery": {"score": 80}},
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201

        list_resp = buying_client.get(
            "/api/v1/suppliers",
            params={"status_badge": "payment_due", "page": 1, "page_size": 20},
            headers=HEADERS,
        )
        assert list_resp.status_code == 200
        listed_row = next(row for row in list_resp.json()["data"] if row["id"] == supplier_id)
        assert listed_row["status_badge"] == "payment_due"
        assert listed_row["summary"]["submitted_purchase_order_count"] == 1
        assert listed_row["summary"]["submitted_purchase_invoice_count"] == 1
        assert listed_row["recommended_action"] == "review_payables"

        detail_resp = buying_client.get(f"/api/v1/suppliers/{supplier_id}", headers=HEADERS)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["summary"]["outstanding_amount"] == 140000.0
        assert detail["available_actions"] == [
            "edit",
            "create_purchase_order",
            "open_purchase_history",
            "open_accounts_payable",
            "view_scorecards",
        ]

        summary_resp = buying_client.get(
            f"/api/v1/suppliers/{supplier_id}/summary",
            headers=HEADERS,
        )
        assert summary_resp.status_code == 200
        summary_payload = summary_resp.json()
        assert summary_payload["status_badge"] == "payment_due"
        assert summary_payload["summary"]["latest_scorecard"]["total_score"] == 72.5

        delete_resp = buying_client.delete(f"/api/v1/suppliers/{supplier_id}", headers=HEADERS)
        assert delete_resp.status_code == 422
        assert "ERR-BUY-046" in delete_resp.text

    def test_구매주문_생성_제출_취소(self, buying_client: httpx.Client) -> None:
        """PurchaseOrder 생성 → 제출 → 취소 워크플로우."""
        # 공급업체 생성
        resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "PO 테스트 공급업체",
                "supplier_type": "individual",
            },
            headers=HEADERS,
        )
        supplier_id = _document_id(resp.json())

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
            headers=HEADERS,
        )
        assert resp.status_code == 201
        po_id = resp.json()["id"]

        # 조회 — 총액 검증
        resp = buying_client.get(f"/api/v1/purchase-orders/{po_id}", headers=HEADERS)
        assert resp.status_code == 200
        po = resp.json()
        assert po["total"] == 50000.0
        assert po["docstatus"] == 0

        # 제출
        resp = buying_client.post(f"/api/v1/purchase-orders/{po_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        # 취소
        resp = buying_client.post(f"/api/v1/purchase-orders/{po_id}/cancel", headers=HEADERS)
        assert resp.status_code == 200

        resp = buying_client.get(f"/api/v1/purchase-orders/{po_id}", headers=HEADERS)
        assert resp.json()["docstatus"] == 2

    def test_견적에서_구매주문을_생성하면_납기와_하위문서요약이_보인다(
        self,
        buying_client: httpx.Client,
    ) -> None:
        """제출된 견적에서 만든 발주는 납기일과 입고/송장 추적 요약을 함께 보여준다."""
        supplier_resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "PO 추적 공급업체",
                "supplier_type": "company",
            },
            headers=HEADERS,
        )
        assert supplier_resp.status_code == 201
        supplier_id = _document_id(supplier_resp.json())

        quotation_resp = buying_client.post(
            "/api/v1/supplier-quotations",
            json={
                "supplier": supplier_id,
                "supplier_name": "PO 추적 공급업체",
                "transaction_date": "2026-04-08",
                "valid_till": "2026-04-30",
                "items": [
                    {
                        "item_code": "ITEM-PO-TRACK-001",
                        "item_name": "추적 대상 원자재",
                        "qty": 10,
                        "rate": 1200,
                    }
                ],
            },
            headers=HEADERS,
        )
        assert quotation_resp.status_code == 201
        quotation_id = _document_id(quotation_resp.json())

        submit_quotation_resp = buying_client.post(
            f"/api/v1/supplier-quotations/{quotation_id}/submit",
            headers=HEADERS,
        )
        assert submit_quotation_resp.status_code == 200

        create_po_resp = buying_client.post(
            f"/api/v1/purchase-orders/from-quotation/{quotation_id}",
            headers=HEADERS,
        )
        assert create_po_resp.status_code == 201
        po_id = create_po_resp.json()["id"]

        submit_po_resp = buying_client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=HEADERS,
        )
        assert submit_po_resp.status_code == 200

        receipt_resp = buying_client.post(
            f"/api/v1/purchase-orders/{po_id}/purchase-receipt",
            headers=HEADERS,
        )
        assert receipt_resp.status_code == 201

        invoice_resp = buying_client.post(
            f"/api/v1/purchase-orders/{po_id}/purchase-invoice",
            headers=HEADERS,
        )
        assert invoice_resp.status_code == 201

        po_resp = buying_client.get(f"/api/v1/purchase-orders/{po_id}", headers=HEADERS)
        assert po_resp.status_code == 200
        po_doc = po_resp.json()
        assert po_doc["items"][0]["delivery_date"] == "2026-04-30"
        assert po_doc["status_badge"] == "submitted"
        assert po_doc["remaining_qty"] == 10.0
        assert po_doc["downstream_summary"] == {
            "purchase_receipt_draft_count": 1,
            "purchase_receipt_submitted_count": 0,
            "purchase_invoice_draft_count": 1,
            "purchase_invoice_submitted_count": 0,
            "has_downstream_documents": True,
        }

    def test_구매입고_상세에서_검수상태와_후속송장요약을_조회한다(
        self,
        buying_client: httpx.Client,
        quality_client: httpx.Client,
    ) -> None:
        """입고 제출 후 검수 대기 상태와 수령 기준 송장 초안 추적을 조회한다."""
        supplier_resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "입고 추적 공급업체",
                "supplier_type": "company",
            },
            headers=HEADERS,
        )
        assert supplier_resp.status_code == 201
        supplier_id = _document_id(supplier_resp.json())

        quotation_resp = buying_client.post(
            "/api/v1/supplier-quotations",
            json={
                "supplier": supplier_id,
                "supplier_name": "입고 추적 공급업체",
                "transaction_date": "2026-04-09",
                "valid_till": "2026-04-30",
                "items": [
                    {
                        "item_code": "ITEM-PRCP-001",
                        "item_name": "입고 추적 자재",
                        "qty": 6,
                        "rate": 2000,
                    }
                ],
            },
            headers=HEADERS,
        )
        assert quotation_resp.status_code == 201
        quotation_id = _document_id(quotation_resp.json())

        submit_quotation_resp = buying_client.post(
            f"/api/v1/supplier-quotations/{quotation_id}/submit",
            headers=HEADERS,
        )
        assert submit_quotation_resp.status_code == 200

        create_po_resp = buying_client.post(
            f"/api/v1/purchase-orders/from-quotation/{quotation_id}",
            headers=HEADERS,
        )
        assert create_po_resp.status_code == 201
        po_id = create_po_resp.json()["id"]

        submit_po_resp = buying_client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=HEADERS,
        )
        assert submit_po_resp.status_code == 200

        create_receipt_resp = buying_client.post(
            f"/api/v1/purchase-orders/{po_id}/purchase-receipt",
            headers=HEADERS,
        )
        assert create_receipt_resp.status_code == 201
        receipt_id = create_receipt_resp.json()["id"]

        receipt_resp = buying_client.get(
            f"/api/v1/purchase-receipts/{receipt_id}",
            headers=HEADERS,
        )
        assert receipt_resp.status_code == 200
        receipt_doc = receipt_resp.json()

        update_resp = buying_client.put(
            f"/api/v1/purchase-receipts/{receipt_id}",
            json={
                "supplier": supplier_id,
                "supplier_name": "입고 추적 공급업체",
                "posting_date": "2026-04-09",
                "items": [
                    {
                        "item_code": receipt_doc["items"][0]["item_code"],
                        "item_name": receipt_doc["items"][0]["item_name"],
                        "qty": receipt_doc["items"][0]["qty"],
                        "rate": receipt_doc["items"][0]["rate"],
                        "warehouse": "WH-RECEIPT-01",
                        "purchase_order": po_id,
                        "inspection_required": True,
                    }
                ],
                "warehouse": "WH-RECEIPT-01",
            },
            headers=HEADERS,
        )
        assert update_resp.status_code == 200

        submit_receipt_resp = buying_client.post(
            f"/api/v1/purchase-receipts/{receipt_id}/submit",
            headers=HEADERS,
        )
        assert submit_receipt_resp.status_code == 200

        inspection_doc = wait_for_condition(
            lambda: next(
                (
                    inspection
                    for inspection in quality_client.get(
                        "/api/v1/quality-inspections",
                        params={"page": 1, "page_size": 50},
                        headers=HEADERS,
                    )
                    .json()
                    .get("data", [])
                    if inspection.get("reference_no") == receipt_id
                ),
                None,
            ),
            timeout=10.0,
            description="입고 제출 후 incoming 품질검사 생성 대기",
        )
        assert inspection_doc["inspection_type"] == "incoming"

        create_invoice_resp = buying_client.post(
            f"/api/v1/purchase-receipts/{receipt_id}/purchase-invoice",
            headers=HEADERS,
        )
        assert create_invoice_resp.status_code == 201
        invoice_id = create_invoice_resp.json()["id"]

        receipt_detail_resp = buying_client.get(
            f"/api/v1/purchase-receipts/{receipt_id}",
            headers=HEADERS,
        )
        assert receipt_detail_resp.status_code == 200
        receipt_detail = receipt_detail_resp.json()
        assert receipt_detail["status_badge"] == "inspection_pending"
        assert receipt_detail["inspection_summary"] == {
            "required_item_count": 1,
            "pending_item_count": 1,
            "completed_item_count": 0,
        }
        assert receipt_detail["downstream_summary"] == {
            "purchase_invoice_draft_count": 1,
            "purchase_invoice_submitted_count": 0,
            "has_downstream_documents": True,
        }
        assert receipt_detail["available_actions"] == [
            "create_purchase_invoice",
            "cancel",
            "view_quality_inspections",
        ]

        receipt_list_resp = buying_client.get(
            "/api/v1/purchase-receipts",
            params={"page": 1, "page_size": 20},
            headers=HEADERS,
        )
        assert receipt_list_resp.status_code == 200
        listed_receipt = next(
            receipt for receipt in receipt_list_resp.json()["data"] if receipt["id"] == receipt_id
        )
        assert listed_receipt["status_badge"] == "inspection_pending"
        assert listed_receipt["downstream_summary"]["purchase_invoice_draft_count"] == 1

        invoice_resp = buying_client.get(
            f"/api/v1/purchase-invoices/{invoice_id}",
            headers=HEADERS,
        )
        assert invoice_resp.status_code == 200
        assert invoice_resp.json()["purchase_receipt_id"] == receipt_id

    def test_구매송장_생성_제출(self, buying_client: httpx.Client) -> None:
        """PurchaseInvoice 생성 → 제출."""
        # 공급업체 생성
        resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "PI 테스트 공급업체",
                "supplier_type": "company",
            },
            headers=HEADERS,
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
            headers=HEADERS,
        )
        assert resp.status_code == 201
        pi_id = resp.json()["id"]

        # 조회
        resp = buying_client.get(f"/api/v1/purchase-invoices/{pi_id}", headers=HEADERS)
        assert resp.status_code == 200
        pi = resp.json()
        assert pi["grand_total"] == 27500.0  # 25000 + 2500

        # 제출
        resp = buying_client.post(f"/api/v1/purchase-invoices/{pi_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        detail_resp = buying_client.get(f"/api/v1/purchase-invoices/{pi_id}", headers=HEADERS)
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["status_badge"] == "submitted_unpaid"
        assert detail["payment_summary"] == {
            "grand_total": 27500.0,
            "outstanding_amount": 27500.0,
            "paid_amount": 0.0,
            "is_paid_in_full": False,
        }
        assert detail["etax_summary"]["transmission_status"] == "pending"
        assert detail["matching_summary"]["match_status"] == "manual_entry"
        assert detail["available_actions"] == [
            "register_payment",
            "open_accounts_payable",
            "open_etax_invoice",
            "submit_etax_to_nts",
            "cancel",
        ]

        list_resp = buying_client.get(
            "/api/v1/purchase-invoices",
            params={"status_badge": "submitted_unpaid", "transmission_status": "pending"},
            headers=HEADERS,
        )
        assert list_resp.status_code == 200
        listed_invoice = next(
            invoice for invoice in list_resp.json()["data"] if invoice["id"] == pi_id
        )
        assert listed_invoice["status_badge"] == "submitted_unpaid"
        assert listed_invoice["matching_summary"]["match_status"] == "manual_entry"

    def test_공급업체견적_워크벤치는_비교순위와_선정상태를_보여준다(
        self,
        buying_client: httpx.Client,
    ) -> None:
        """공급업체 견적 목록/상세는 RFQ 비교 맥락과 발주 선정 상태를 함께 제공한다."""
        supplier_a_resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "워크벤치 공급업체 A",
                "supplier_type": "company",
            },
            headers=HEADERS,
        )
        assert supplier_a_resp.status_code == 201
        supplier_a_id = supplier_a_resp.json()["_id"]

        supplier_b_resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "워크벤치 공급업체 B",
                "supplier_type": "company",
            },
            headers=HEADERS,
        )
        assert supplier_b_resp.status_code == 201
        supplier_b_id = supplier_b_resp.json()["_id"]

        rfq_resp = buying_client.post(
            "/api/v1/request-for-quotations",
            json={
                "transaction_date": "2026-04-10",
                "suppliers": [supplier_a_id, supplier_b_id],
                "items": [
                    {
                        "item_code": "ITEM-SQ-WB-001",
                        "item_name": "워크벤치 대상 자재",
                        "qty": 12,
                    }
                ],
            },
            headers=HEADERS,
        )
        assert rfq_resp.status_code == 201
        rfq_id = rfq_resp.json()["id"]

        submit_rfq_resp = buying_client.post(
            f"/api/v1/request-for-quotations/{rfq_id}/submit",
            headers=HEADERS,
        )
        assert submit_rfq_resp.status_code == 200

        quotation_a_resp = buying_client.post(
            "/api/v1/supplier-quotations",
            json={
                "rfq_reference": rfq_id,
                "supplier": supplier_a_id,
                "supplier_name": "워크벤치 공급업체 A",
                "transaction_date": "2026-04-10",
                "valid_till": "2026-04-25",
                "items": [
                    {
                        "item_code": "ITEM-SQ-WB-001",
                        "item_name": "워크벤치 대상 자재",
                        "qty": 12,
                        "rate": 5100,
                    }
                ],
            },
            headers=HEADERS,
        )
        assert quotation_a_resp.status_code == 201
        quotation_a_id = quotation_a_resp.json()["id"]

        quotation_b_resp = buying_client.post(
            "/api/v1/supplier-quotations",
            json={
                "rfq_reference": rfq_id,
                "supplier": supplier_b_id,
                "supplier_name": "워크벤치 공급업체 B",
                "transaction_date": "2026-04-10",
                "valid_till": "2026-04-25",
                "items": [
                    {
                        "item_code": "ITEM-SQ-WB-001",
                        "item_name": "워크벤치 대상 자재",
                        "qty": 12,
                        "rate": 4900,
                    }
                ],
            },
            headers=HEADERS,
        )
        assert quotation_b_resp.status_code == 201
        quotation_b_id = quotation_b_resp.json()["id"]

        for quotation_id in (quotation_a_id, quotation_b_id):
            submit_resp = buying_client.post(
                f"/api/v1/supplier-quotations/{quotation_id}/submit",
                headers=HEADERS,
            )
            assert submit_resp.status_code == 200

        workbench_resp = buying_client.get(
            "/api/v1/supplier-quotations",
            params={"rfq_reference": rfq_id, "status_badge": "best_offer"},
            headers=HEADERS,
        )
        assert workbench_resp.status_code == 200
        workbench = workbench_resp.json()
        assert workbench["total"] == 1
        best_offer_row = workbench["data"][0]
        assert best_offer_row["id"] == quotation_b_id
        assert best_offer_row["status_badge"] == "best_offer"
        assert best_offer_row["summary"] == {
            "item_count": 1,
            "total_qty": 12.0,
            "submitted_quote_count": 2,
            "rfq_supplier_count": 2,
            "comparison_rank": 1,
            "linked_purchase_order_count": 0,
            "is_lowest_quote": True,
        }
        assert best_offer_row["recommended_action"] == "create_purchase_order"
        assert best_offer_row["available_actions"] == [
            "compare_quotations",
            "create_purchase_order",
            "view_rfq",
            "cancel",
        ]

        detail_resp = buying_client.get(
            f"/api/v1/supplier-quotations/{quotation_b_id}",
            headers=HEADERS,
        )
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert detail["status_badge"] == "best_offer"
        assert detail["summary"]["comparison_rank"] == 1

        summary_resp = buying_client.get(
            f"/api/v1/supplier-quotations/{quotation_b_id}/summary",
            headers=HEADERS,
        )
        assert summary_resp.status_code == 200
        summary = summary_resp.json()
        assert summary["status_badge"] == "best_offer"
        assert summary["summary"]["linked_purchase_order_count"] == 0

        create_po_resp = buying_client.post(
            f"/api/v1/purchase-orders/from-quotation/{quotation_b_id}",
            headers=HEADERS,
        )
        assert create_po_resp.status_code == 201
        po_id = create_po_resp.json()["id"]
        assert po_id

        selected_detail_resp = buying_client.get(
            f"/api/v1/supplier-quotations/{quotation_b_id}",
            headers=HEADERS,
        )
        assert selected_detail_resp.status_code == 200
        selected_detail = selected_detail_resp.json()
        assert selected_detail["status_badge"] == "selected_for_order"
        assert selected_detail["recommended_action"] == "review_purchase_order"
        assert selected_detail["summary"]["linked_purchase_order_count"] == 1
        assert selected_detail["available_actions"] == [
            "compare_quotations",
            "open_purchase_order",
            "view_rfq",
            "cancel",
        ]

    def test_구매분석_워크벤치는_KPI와_차트번들을_반환한다(
        self,
        buying_client: httpx.Client,
    ) -> None:
        """구매 분석 대시보드는 제출 문서를 기준으로 KPI/차트/공급업체 랭킹을 제공한다."""
        supplier_a_resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "구매분석 공급업체 A",
                "supplier_type": "company",
            },
            headers=HEADERS,
        )
        assert supplier_a_resp.status_code == 201
        supplier_a_id = supplier_a_resp.json()["_id"]

        supplier_b_resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "구매분석 공급업체 B",
                "supplier_type": "company",
            },
            headers=HEADERS,
        )
        assert supplier_b_resp.status_code == 201
        supplier_b_id = supplier_b_resp.json()["_id"]

        for supplier_id, supplier_name, transaction_date, qty, rate in (
            (supplier_a_id, "구매분석 공급업체 A", "2026-04-05", 12, 10000),
            (supplier_b_id, "구매분석 공급업체 B", "2026-03-14", 4, 12000),
        ):
            po_resp = buying_client.post(
                "/api/v1/purchase-orders",
                json={
                    "supplier_id": supplier_id,
                    "supplier_name": supplier_name,
                    "transaction_date": transaction_date,
                    "items": [
                        {
                            "item_code": f"ITEM-{supplier_id[-4:]}",
                            "item_name": f"{supplier_name} 자재",
                            "qty": qty,
                            "rate": rate,
                        }
                    ],
                },
                headers=HEADERS,
            )
            assert po_resp.status_code == 201
            po_id = po_resp.json()["id"]
            submit_po_resp = buying_client.post(
                f"/api/v1/purchase-orders/{po_id}/submit",
                headers=HEADERS,
            )
            assert submit_po_resp.status_code == 200

        for supplier_id, supplier_name, posting_date, due_date, qty, rate in (
            (supplier_a_id, "구매분석 공급업체 A", "2026-04-10", "2020-01-01", 8, 11000),
            (supplier_b_id, "구매분석 공급업체 B", "2026-03-20", "2099-01-01", 3, 9000),
        ):
            invoice_resp = buying_client.post(
                "/api/v1/purchase-invoices",
                json={
                    "supplier_id": supplier_id,
                    "supplier_name": supplier_name,
                    "posting_date": posting_date,
                    "due_date": due_date,
                    "items": [
                        {
                            "item_code": f"ITEM-{supplier_id[-4:]}",
                            "item_name": f"{supplier_name} 자재",
                            "qty": qty,
                            "rate": rate,
                        }
                    ],
                    "taxes": [],
                },
                headers=HEADERS,
            )
            assert invoice_resp.status_code == 201
            invoice_id = invoice_resp.json()["id"]
            submit_invoice_resp = buying_client.post(
                f"/api/v1/purchase-invoices/{invoice_id}/submit",
                headers=HEADERS,
            )
            assert submit_invoice_resp.status_code == 200

        analytics_resp = buying_client.get(
            "/api/v1/purchase-analytics",
            params={"group_by": "supplier", "status_badge": "payment_due"},
            headers=HEADERS,
        )
        assert analytics_resp.status_code == 200
        analytics = analytics_resp.json()
        assert analytics["total"] == 1
        assert analytics["summary"] == {
            "submitted_purchase_order_count": 2,
            "purchase_order_amount_total": 168000.0,
            "submitted_purchase_invoice_count": 2,
            "purchase_invoice_amount_total": 115000.0,
            "active_supplier_count": 2,
            "open_purchase_order_count": 2,
            "overdue_payable_count": 1,
            "best_supplier_name": "구매분석 공급업체 A",
            "best_supplier_amount": 88000.0,
        }
        assert analytics["recommended_action"] == "review_overdue_payables"
        assert analytics["available_actions"] == [
            "open_purchase_orders",
            "open_purchase_invoices",
            "open_suppliers",
            "review_supplier_scorecards",
        ]
        first_row = analytics["data"][0]
        assert first_row["group_key"] == supplier_a_id
        assert first_row["status_badge"] == "payment_due"
        assert first_row["recommended_action"] == "review_payables"
        assert first_row["summary"]["overdue_payable_count"] == 1
        trend = analytics["charts"]["purchase_trend"]
        assert trend == [
            {
                "period": "2026-03",
                "ordered_amount": 48000.0,
                "invoiced_amount": 27000.0,
                "qty": 4.0,
            },
            {
                "period": "2026-04",
                "ordered_amount": 120000.0,
                "invoiced_amount": 88000.0,
                "qty": 12.0,
            },
        ]
        assert analytics["charts"]["supplier_mix"][0]["supplier_name"] == "구매분석 공급업체 A"
        pipeline = {row["status"]: row["count"] for row in analytics["charts"]["payable_pipeline"]}
        assert pipeline == {"overdue": 1, "open": 1}

    def test_구매주문_목록_페이지네이션(self, buying_client: httpx.Client) -> None:
        """목록 조회 페이지네이션 동작 검증."""
        resp = buying_client.get(
            "/api/v1/purchase-orders",
            params={"page": 1, "page_size": 5},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "total" in body
