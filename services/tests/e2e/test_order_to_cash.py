"""Order-to-Cash E2E 테스트 — 판매주문→출고→송장→수금.

전체 수주-매출 사이클을 서비스 API 호출로 검증한다.
selling → stock → accounting 서비스 간 데이터 흐름을 확인한다.
"""

from __future__ import annotations

import httpx
import pytest

from tests.e2e.conftest import wait_for_condition
from tests.e2e.helpers.api_client import HEADERS

pytestmark = pytest.mark.e2e

# 폴링 최대 횟수
_POLL_MAX = 10
# 폴링 간격 (초)
_POLL_INTERVAL = 0.5


def _poll_until(
    client: httpx.Client,
    url: str,
    *,
    check: str,
    expected: object,
    timeout: float = _POLL_MAX * _POLL_INTERVAL,
) -> dict:
    """응답의 특정 필드가 기대값이 될 때까지 폴링한다."""

    def _check():
        resp = client.get(url, headers=HEADERS)
        if resp.status_code == 200:
            body = resp.json()
            # 목록 응답인 경우 data 필드 확인
            if "data" in body and isinstance(body["data"], list) and len(body["data"]) > 0:
                if body["data"][0].get(check) == expected:
                    return body
            # 단건 응답인 경우
            elif body.get(check) == expected:
                return body
        return None

    return wait_for_condition(
        _check,
        timeout=timeout,
        interval=_POLL_INTERVAL,
        description=f"{url}에서 {check}=={expected} 대기",
    )


class TestOrderToCash:
    """판매주문 → 출고 → 송장 → 수금 전체 사이클을 검증한다."""

    def test_수주_매출_전체_흐름(
        self,
        selling_client: httpx.Client,
        stock_client: httpx.Client,
        accounting_client: httpx.Client,
    ) -> None:
        """수주→출고→매출송장→분개검증→수금→AR 소거까지 전체 흐름."""
        # --- Step 1: 고객 생성 (selling 서비스) ---
        resp = selling_client.post(
            "/api/v1/customers",
            json={
                "customer_name": "OTC E2E 고객",
                "customer_type": "company",
                "tax_id": "111-22-33333",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        customer = resp.json()
        customer_id = customer["_id"]

        # --- Step 2: 품목 생성 (stock 서비스) ---
        resp = stock_client.post(
            "/api/v1/items",
            json={
                "item_name": "OTC 테스트 제품",
                "item_group": "완제품",
                "stock_uom": "EA",
                "is_stock_item": True,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        item = resp.json()
        item_code = item["item_code"]

        # --- Step 3: 입고 — 테스트용 재고 확보 (stock 서비스) ---
        resp = stock_client.post(
            "/api/v1/purchase-receipts",
            json={
                "supplier_name": "OTC 입고 공급사",
                "posting_date": "2026-03-20",
                "items": [
                    {
                        "item_code": item_code,
                        "item_name": "OTC 테스트 제품",
                        "qty": 100,
                        "rate": 5000,
                        "warehouse": "메인 창고",
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        pr_id = resp.json().get("_id") or resp.json().get("id")

        # 입고 제출
        resp = stock_client.post(
            f"/api/v1/purchase-receipts/{pr_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # --- Step 4: 판매주문 생성 + 제출 ---
        resp = selling_client.post(
            "/api/v1/sales-orders",
            json={
                "customer_id": customer_id,
                "customer_name": "OTC E2E 고객",
                "transaction_date": "2026-03-20",
                "delivery_date": "2026-03-25",
                "items": [
                    {
                        "item_code": item_code,
                        "item_name": "OTC 테스트 제품",
                        "qty": 10,
                        "rate": 10000,
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        so_id = resp.json().get("_id") or resp.json().get("id")

        # 판매주문 조회 — 총액 검증
        resp = selling_client.get(
            f"/api/v1/sales-orders/{so_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        so = resp.json()
        assert so["total"] == 100000.0  # 10 * 10000

        # 판매주문 제출
        resp = selling_client.post(
            f"/api/v1/sales-orders/{so_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # --- Step 5: 납품서 생성 + 제출 ---
        resp = selling_client.post(
            "/api/v1/delivery-notes",
            json={
                "customer_id": customer_id,
                "customer_name": "OTC E2E 고객",
                "posting_date": "2026-03-22",
                "sales_order_id": so_id,
                "items": [
                    {
                        "item_code": item_code,
                        "item_name": "OTC 테스트 제품",
                        "qty": 10,
                        "warehouse": "메인 창고",
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        dn_id = resp.json().get("_id") or resp.json().get("id")

        # 납품서 제출
        resp = selling_client.post(
            f"/api/v1/delivery-notes/{dn_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # --- Step 6: 매출송장 생성 + 제출 ---
        tax_amount = 10000.0  # 부가세 10%
        net_total = 100000.0  # 10 * 10000
        grand_total = net_total + tax_amount  # 110000

        resp = selling_client.post(
            "/api/v1/sales-invoices",
            json={
                "customer_id": customer_id,
                "customer_name": "OTC E2E 고객",
                "posting_date": "2026-03-22",
                "due_date": "2026-04-22",
                "sales_order_id": so_id,
                "delivery_note_id": dn_id,
                "items": [
                    {
                        "item_code": item_code,
                        "item_name": "OTC 테스트 제품",
                        "qty": 10,
                        "rate": 10000,
                    },
                ],
                "taxes": [
                    {"tax_type": "부가세", "rate": 10, "amount": tax_amount},
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        sinv = resp.json()
        sinv_id = sinv["id"]

        # 매출송장 조회 — grand_total 검증
        resp = selling_client.get(
            f"/api/v1/sales-invoices/{sinv_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["grand_total"] == grand_total

        # 매출송장 제출
        resp = selling_client.post(
            f"/api/v1/sales-invoices/{sinv_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # --- 검증: 분개전표 자동 생성 확인 (accounting 서비스) ---
        def _분개전표_생성_확인():
            resp = accounting_client.get(
                "/api/v1/journal-entries",
                params={"voucher_no": sinv_id},
                headers=HEADERS,
            )
            data = resp.json()
            return resp.status_code == 200 and data.get("total", 0) > 0

        wait_for_condition(
            _분개전표_생성_확인,
            timeout=10.0,
            description="분개전표 자동생성 대기",
        )
        resp = accounting_client.get(
            "/api/v1/journal-entries",
            params={"voucher_no": sinv_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        je_data = resp.json()
        assert je_data["total"] > 0, "매출송장 제출 후 분개전표가 자동 생성되어야 합니다"
        je = je_data["data"][0]
        assert je["total_debit"] == je["total_credit"]

        # --- 검증: AR(매출채권) 생성 확인 ---
        def _매출채권_생성_확인():
            resp = accounting_client.get(
                "/api/v1/accounts-receivable",
                params={"voucher_no": sinv_id},
                headers=HEADERS,
            )
            data = resp.json()
            return resp.status_code == 200 and data.get("total", 0) > 0

        wait_for_condition(
            _매출채권_생성_확인,
            timeout=10.0,
            description="매출채권(AR) 생성 대기",
        )
        resp = accounting_client.get(
            "/api/v1/accounts-receivable",
            params={"voucher_no": sinv_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        ar_data = resp.json()
        assert ar_data["total"] > 0, "매출송장 제출 후 매출채권이 생성되어야 합니다"
        ar = ar_data["data"][0]
        assert ar["outstanding_amount"] == grand_total

        # --- Step 7: 수금 생성 + 제출 ---
        resp = accounting_client.post(
            "/api/v1/payment-entries",
            json={
                "payment_type": "receive",
                "party_type": "customer",
                "party_id": customer_id,
                "party_name": "OTC E2E 고객",
                "posting_date": "2026-03-25",
                "paid_amount": grand_total,
                "received_amount": grand_total,
                "reference_doctype": "sales_invoice",
                "reference_name": sinv_id,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        pe_id = resp.json().get("_id") or resp.json().get("id")

        # 수금 제출
        resp = accounting_client.post(
            f"/api/v1/payment-entries/{pe_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # --- 검증: AR outstanding_amount == 0 ---
        def _매출채권_소거_확인():
            resp = accounting_client.get(
                "/api/v1/accounts-receivable",
                params={"voucher_no": sinv_id},
                headers=HEADERS,
            )
            if resp.status_code != 200:
                return False
            data = resp.json()
            if data.get("total", 0) <= 0:
                return False
            return data["data"][0].get("outstanding_amount") == 0

        wait_for_condition(
            _매출채권_소거_확인,
            timeout=10.0,
            description="매출채권(AR) 소거 대기",
        )
        resp = accounting_client.get(
            "/api/v1/accounts-receivable",
            params={"voucher_no": sinv_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        ar_data = resp.json()
        assert ar_data["total"] > 0, "수금 후에도 매출채권 레코드가 존재해야 합니다"
        ar = ar_data["data"][0]
        assert ar["outstanding_amount"] == 0, "수금 후 매출채권 잔액이 0이어야 합니다"
