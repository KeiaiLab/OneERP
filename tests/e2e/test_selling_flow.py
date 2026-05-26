"""E2E: 판매 플로우 — Customer → Quotation → SalesOrder → DeliveryNote → SalesInvoice."""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.helpers.api_client import HEADERS

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

    def test_가격표_워크벤치와_견적_자동단가_적용(self, selling_client: httpx.Client) -> None:
        """가격표는 카탈로그/워크벤치와 견적 자동단가 적용을 함께 제공해야 한다."""
        resp = selling_client.post(
            "/api/v1/customer-groups",
            json={"group_name": "VIP", "default_price_list": ""},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        customer_group_id = resp.json()["_id"]

        resp = selling_client.post(
            "/api/v1/price-lists",
            json={
                "price_list_name": "VIP USD",
                "currency": "USD",
                "selling": True,
                "customer_group": "VIP",
                "valid_from": "2026-04-01",
                "valid_to": "2026-12-31",
                "items": [
                    {
                        "item_code": "ITEM-USD",
                        "item_name": "수출 상품",
                        "price": "120",
                        "min_qty": "1",
                    },
                    {
                        "item_code": "ITEM-USD",
                        "item_name": "수출 상품",
                        "price": "110",
                        "min_qty": "20",
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        price_list = resp.json()
        price_list_id = price_list["_id"]

        resp = selling_client.put(
            f"/api/v1/customer-groups/{customer_group_id}",
            json={"default_price_list": price_list_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = selling_client.get(
            "/api/v1/price-lists/catalog",
            params={"customer_group": "VIP", "currency": "USD", "transaction_date": "2026-04-09"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        catalog = resp.json()
        assert catalog["total"] == 1
        assert catalog["data"][0]["id"] == price_list_id

        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "가격표 테스트 고객",
                "customer_type": "company",
                "default_currency": "USD",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        customer_id = resp.json()["_id"]

        resp = selling_client.post(
            "/api/v1/quotations",
            json={
                "customer_id": customer_id,
                "customer_name": "가격표 테스트 고객",
                "transaction_date": "2026-04-09",
                "valid_till": "2026-04-30",
                "price_list_id": price_list_id,
                "items": [
                    {"item_code": "ITEM-USD", "item_name": "수출 상품", "qty": 25, "rate": 0},
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        quotation_id = resp.json()["id"]

        resp = selling_client.get(f"/api/v1/quotations/{quotation_id}", headers=HEADERS)
        assert resp.status_code == 200
        quotation = resp.json()
        assert quotation["price_list_id"] == price_list_id
        assert quotation["price_list_name"] == "VIP USD"
        assert quotation["currency"] == "USD"
        assert quotation["items"][0]["rate"] == 110.0
        assert quotation["total"] == 2750.0

        resp = selling_client.get(f"/api/v1/price-lists/{price_list_id}", headers=HEADERS)
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["status_badge"] == "active_in_use"
        assert detail["usage_summary"]["customer_group_count"] == 1
        assert detail["usage_summary"]["quotation_count"] == 1
        assert detail["rate_summary"]["tiered_item_count"] == 1

    def test_판매분석_워크벤치는_KPI와_차트번들을_반환한다(
        self, selling_client: httpx.Client
    ) -> None:
        """판매 분석은 KPI 카드, 차트 번들, 고객 랭킹 액션을 한 응답으로 제공해야 한다."""
        resp = selling_client.post(
            "/api/v1/customers",
            json={"customer_name": "분석 고객 A", "customer_type": "company"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        customer_a = resp.json()["_id"]

        resp = selling_client.post(
            "/api/v1/customers",
            json={"customer_name": "분석 고객 B", "customer_type": "company"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        customer_b = resp.json()["_id"]

        for customer_id, customer_name, posting_date, item_code, item_name, qty, rate in [
            (customer_a, "분석 고객 A", "2026-02-10", "ITEM-A", "A 품목", 4, 25000),
            (customer_b, "분석 고객 B", "2026-01-05", "ITEM-B", "B 품목", 2, 30000),
        ]:
            resp = selling_client.post(
                "/api/v1/sales-invoices",
                json={
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    "posting_date": posting_date,
                    "due_date": "2026-05-15",
                    "items": [
                        {
                            "item_code": item_code,
                            "item_name": item_name,
                            "qty": qty,
                            "rate": rate,
                        }
                    ],
                    "taxes": [],
                },
                headers=HEADERS,
            )
            assert resp.status_code == 201
            invoice_id = resp.json()["id"]
            resp = selling_client.post(
                f"/api/v1/sales-invoices/{invoice_id}/submit", headers=HEADERS
            )
            assert resp.status_code == 200

        resp = selling_client.post(
            "/api/v1/quotations",
            json={
                "customer_id": customer_a,
                "customer_name": "분석 고객 A",
                "transaction_date": "2026-02-01",
                "valid_till": "2026-02-28",
                "items": [{"item_code": "ITEM-A", "item_name": "A 품목", "qty": 1, "rate": 50000}],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        quotation_id = resp.json()["id"]
        resp = selling_client.post(f"/api/v1/quotations/{quotation_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        resp = selling_client.get(
            "/api/v1/sales-analytics",
            params={
                "group_by": "customer",
                "period_from": "2026-01-01",
                "period_to": "2026-02-28",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200
        analytics = resp.json()

        assert analytics["summary"]["submitted_invoice_count"] == 2
        assert analytics["summary"]["invoice_amount_total"] == 160000.0
        assert analytics["summary"]["open_quotation_count"] == 1
        assert analytics["summary"]["stale_quotation_count"] == 1
        assert analytics["summary"]["best_customer_name"] == "분석 고객 A"
        assert analytics["recommended_action"] == "review_stale_quotations"
        assert analytics["charts"]["sales_trend"] == [
            {"period": "2026-01", "amount": 60000.0, "qty": 2.0},
            {"period": "2026-02", "amount": 100000.0, "qty": 4.0},
        ]
        first_row = analytics["data"][0]
        assert first_row["group_key"] == customer_a
        assert first_row["status_badge"] == "top_customer"
        assert first_row["recommended_action"] == "expand_account_plan"

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

        # 제출 문서는 삭제할 수 없어야 한다.
        resp = selling_client.delete(f"/api/v1/quotations/{qtn_id}")
        assert resp.status_code == 400

        # 취소
        resp = selling_client.post(f"/api/v1/quotations/{qtn_id}/cancel")
        assert resp.status_code == 200

        resp = selling_client.get(f"/api/v1/quotations/{qtn_id}")
        assert resp.json()["docstatus"] == 2  # CANCELLED

    def test_견적서_메일발송_PDF_전자서명(self, selling_client: httpx.Client) -> None:
        """제출된 견적서를 메일 발송하고 PDF/포털 전자서명 흐름을 검증한다."""
        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "서명 테스트 고객",
                "customer_type": "company",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        customer_id = resp.json()["_id"]

        resp = selling_client.post(
            "/api/v1/quotations",
            json={
                "customer_id": customer_id,
                "customer_name": "서명 테스트 고객",
                "transaction_date": "2026-04-08",
                "valid_till": "2026-04-30",
                "items": [
                    {
                        "item_code": "ITEM-SIGN",
                        "item_name": "전자서명 상품",
                        "qty": 1,
                        "rate": 44000,
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        qtn_id = resp.json()["id"]

        resp = selling_client.post(f"/api/v1/quotations/{qtn_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        resp = selling_client.post(
            f"/api/v1/quotations/{qtn_id}/send-email",
            json={
                "recipient_email": "customer@example.com",
                "subject": "견적서 확인 요청",
                "message": "PDF와 서명 링크를 확인해 주세요.",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200
        delivery = resp.json()
        assert delivery["recipient_email"] == "customer@example.com"
        assert delivery["pdf_download_url"].endswith(f"/api/v1/quotations/{qtn_id}/pdf")

        resp = selling_client.get(delivery["pdf_download_url"], headers=HEADERS)
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("application/pdf")

        resp = selling_client.post(
            f"/api/v1/portal/quotations/{qtn_id}/sign",
            params={"tenant_id": HEADERS["X-Tenant-Id"]},
            json={
                "token": delivery["portal_access_token"],
                "signer_name": "김고객",
                "signer_email": "customer@example.com",
                "signature_text": "김고객",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["signature_status"] == "signed"

        resp = selling_client.get(f"/api/v1/quotations/{qtn_id}", headers=HEADERS)
        assert resp.status_code == 200
        assert resp.json()["signature_status"] == "signed"

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

    def test_판매주문_후속문서_요약_추적(self, selling_client: httpx.Client) -> None:
        """제출된 판매주문이 납품서/송장 추적과 상태 배지를 함께 반환한다."""
        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "SO 추적 테스트 고객",
                "customer_type": "company",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        customer_id = resp.json()["_id"]

        resp = selling_client.post(
            "/api/v1/sales-orders",
            json={
                "customer_id": customer_id,
                "customer_name": "SO 추적 테스트 고객",
                "transaction_date": "2026-04-10",
                "delivery_date": "2026-04-12",
                "items": [
                    {"item_code": "ITEM-A", "item_name": "품목 A", "qty": 5, "rate": 2000},
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        so_id = resp.json()["id"]

        resp = selling_client.post(f"/api/v1/sales-orders/{so_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        resp = selling_client.post(
            f"/api/v1/sales-orders/{so_id}/delivery-note",
            json={"warehouse": "WH-001"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        dn_id = resp.json()["id"]
        assert resp.json()["downstream_summary"]["delivery_note_count"] == 1

        resp = selling_client.post(
            f"/api/v1/sales-orders/{so_id}/sales-invoice",
            json={
                "posting_date": "2026-04-12",
                "due_date": "2026-05-12",
                "taxes": [{"tax_type": "부가세", "rate": 10, "amount": 1000}],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        sinv_id = resp.json()["id"]
        assert resp.json()["downstream_summary"]["sales_invoice_count"] == 1

        resp = selling_client.get(f"/api/v1/sales-orders/{so_id}", headers=HEADERS)
        assert resp.status_code == 200
        sales_order = resp.json()
        assert sales_order["status_badge"] == "submitted"
        assert sales_order["downstream_refs"]["delivery_note_ids"] == [dn_id]
        assert sales_order["downstream_refs"]["sales_invoice_ids"] == [sinv_id]
        assert sales_order["downstream_summary"] == {
            "delivery_note_count": 1,
            "sales_invoice_count": 1,
            "has_downstream_documents": True,
        }

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

    def test_납품서_상태배지와_후속송장_요약을_조회한다(self, selling_client: httpx.Client) -> None:
        """납품서 상세/목록이 상태 배지와 후속 송장 요약을 제공한다."""
        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "배송 추적 고객",
                "customer_type": "company",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        customer_id = resp.json()["_id"]

        resp = selling_client.post(
            "/api/v1/delivery-notes",
            json={
                "customer_id": customer_id,
                "customer_name": "배송 추적 고객",
                "posting_date": "2026-04-18",
                "sales_order_ref": "SO-TRACE-001",
                "transporter": "대한통운",
                "items": [
                    {
                        "item_code": "ITEM-DN-TRACE-001",
                        "item_name": "배송 추적 품목",
                        "qty": 2,
                        "rate": 15000,
                        "warehouse": "WH-001",
                    }
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        dn_id = resp.json()["id"]

        resp = selling_client.post(f"/api/v1/delivery-notes/{dn_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        resp = selling_client.post(
            f"/api/v1/delivery-notes/{dn_id}/sales-invoice",
            json={
                "posting_date": "2026-04-19",
                "due_date": "2026-05-19",
                "taxes": [{"tax_type": "VAT", "rate": 10, "amount": 3000}],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        invoice_id = resp.json()["id"]
        assert resp.json()["downstream_summary"]["sales_invoice_count"] == 1

        resp = selling_client.get(f"/api/v1/delivery-notes/{dn_id}", headers=HEADERS)
        assert resp.status_code == 200
        delivery_note = resp.json()
        assert delivery_note["status_badge"] == "submitted"
        assert delivery_note["downstream_refs"]["sales_invoice_ids"] == [invoice_id]
        assert delivery_note["downstream_summary"] == {
            "sales_invoice_count": 1,
            "has_downstream_documents": True,
        }
        assert delivery_note["available_actions"] == ["create_sales_invoice", "cancel"]

        resp = selling_client.get(
            "/api/v1/delivery-notes",
            params={
                "status_badge": "submitted",
                "sales_order_ref": "SO-TRACE-001",
                "transporter": "대한통운",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["total"] == 1
        assert payload["data"][0]["id"] == dn_id
        assert payload["data"][0]["downstream_summary"]["sales_invoice_count"] == 1

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

    def test_매출송장_상태배지와_전자세금계산서_요약을_조회한다(
        self,
        selling_client: httpx.Client,
    ) -> None:
        """판매송장 상세/목록이 수금 상태와 전자세금계산서 요약을 함께 제공한다."""
        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "세금계산서 고객",
                "customer_type": "company",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        customer_id = resp.json()["_id"]

        resp = selling_client.post(
            "/api/v1/sales-invoices",
            json={
                "customer_id": customer_id,
                "customer_name": "세금계산서 고객",
                "posting_date": "2026-04-09",
                "due_date": "2026-05-09",
                "sales_order_ref": "SO-TAX-001",
                "delivery_note_ref": "DN-TAX-001",
                "items": [
                    {
                        "item_code": "ITEM-TAX",
                        "item_name": "세금계산 품목",
                        "qty": 1,
                        "rate": 100000,
                    },
                ],
                "taxes": [
                    {"tax_type": "부가세", "rate": 10, "amount": 10000},
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        sinv_id = resp.json()["id"]

        resp = selling_client.post(f"/api/v1/sales-invoices/{sinv_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        resp = selling_client.get(f"/api/v1/sales-invoices/{sinv_id}", headers=HEADERS)
        assert resp.status_code == 200
        invoice = resp.json()
        assert invoice["status_badge"] == "submitted_unpaid"
        assert invoice["payment_summary"] == {
            "grand_total": 110000.0,
            "outstanding_amount": 110000.0,
            "collected_amount": 0.0,
            "is_paid_in_full": False,
        }
        assert invoice["etax_summary"]["transmission_status"] == "pending"
        assert invoice["available_actions"] == [
            "register_payment",
            "open_accounts_receivable",
            "open_etax_invoice",
            "submit_etax_to_nts",
            "cancel",
        ]

        resp = selling_client.get(
            "/api/v1/sales-invoices",
            params={
                "customer_id": customer_id,
                "status_badge": "submitted_unpaid",
                "transmission_status": "pending",
                "sales_order_ref": "SO-TAX-001",
                "delivery_note_ref": "DN-TAX-001",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["total"] == 1
        assert payload["data"][0]["id"] == sinv_id
        assert payload["data"][0]["status_badge"] == "submitted_unpaid"
        assert payload["data"][0]["etax_summary"]["transmission_status"] == "pending"

    def test_견적서_목록_페이지네이션(self, selling_client: httpx.Client) -> None:
        """목록 조회 페이지네이션 파라미터가 동작한다."""
        resp = selling_client.get("/api/v1/quotations", params={"page": 1, "page_size": 5})
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body
        assert "total" in body
        assert body["page"] == 1
        assert body["page_size"] == 5

    def test_판매파트너_거래이력_워크벤치를_조회한다(self, selling_client: httpx.Client) -> None:
        """고객 재배정 이후에도 판매파트너 상세가 거래 스냅샷 기반 실적을 유지한다."""
        resp = selling_client.post(
            "/api/v1/sales-partners",
            json={
                "partner_name": "유통 파트너 A",
                "commission_rate": 7.5,
                "territory": "서울",
                "partner_type": "distributor",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        partner_payload = resp.json()
        partner_id = partner_payload.get("id") or partner_payload["_id"]

        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "판매파트너 고객",
                "customer_type": "company",
                "territory": "서울",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        customer_id = resp.json()["_id"]

        resp = selling_client.post(
            f"/api/v1/sales-partners/{partner_id}/customers/{customer_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = selling_client.post(
            "/api/v1/sales-orders",
            json={
                "customer_id": customer_id,
                "customer_name": "판매파트너 고객",
                "transaction_date": "2026-04-10",
                "delivery_date": "2026-04-12",
                "items": [
                    {
                        "item_code": "ITEM-PARTNER",
                        "item_name": "파트너 상품",
                        "qty": 2,
                        "rate": 50000,
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        so_id = resp.json()["id"]

        resp = selling_client.post(f"/api/v1/sales-orders/{so_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        resp = selling_client.post(
            f"/api/v1/sales-orders/{so_id}/sales-invoice",
            json={"posting_date": "2026-04-12", "due_date": "2026-04-30"},
            headers=HEADERS,
        )
        assert resp.status_code == 201
        invoice_id = resp.json()["id"]

        resp = selling_client.post(f"/api/v1/sales-invoices/{invoice_id}/submit", headers=HEADERS)
        assert resp.status_code == 200

        resp = selling_client.delete(
            f"/api/v1/sales-partners/{partner_id}/customers/{customer_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        resp = selling_client.get(
            "/api/v1/sales-partners?status_badge=active_collection_risk&territory=서울",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        listing = resp.json()
        assert listing["total"] == 1
        assert listing["data"][0]["status_badge"] == "active_collection_risk"
        assert listing["data"][0]["summary"]["linked_customer_count"] == 0
        assert listing["data"][0]["summary"]["historical_customer_count"] == 1

        resp = selling_client.get(f"/api/v1/sales-partners/{partner_id}", headers=HEADERS)
        assert resp.status_code == 200
        detail = resp.json()
        assert detail["summary"]["submitted_invoice_count"] == 1
        assert detail["summary"]["submitted_sales_amount"] == 100000.0
        assert detail["summary"]["expected_commission_amount"] == 7500.0
        assert detail["recommended_action"] == "review_receivables"

        resp = selling_client.delete(f"/api/v1/sales-partners/{partner_id}", headers=HEADERS)
        assert resp.status_code == 422
        assert resp.json()["error"] == "ERR-SELL-044"
