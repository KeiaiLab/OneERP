"""Procure-to-Pay E2E 테스트 — 구매주문→입고→송장→지급.

전체 구매-지급 사이클을 서비스 API 호출로 검증한다.
buying → stock → accounting 서비스 간 데이터 흐름을 확인한다.
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
            if "data" in body and isinstance(body["data"], list) and len(body["data"]) > 0:
                if body["data"][0].get(check) == expected:
                    return body
            elif body.get(check) == expected:
                return body
        return None

    return wait_for_condition(
        _check,
        timeout=timeout,
        interval=_POLL_INTERVAL,
        description=f"{url}에서 {check}=={expected} 대기",
    )


class TestProcureToPay:
    """구매주문 → 입고 → 구매송장 → 지급 전체 사이클을 검증한다."""

    def test_구매_지급_전체_흐름(
        self,
        buying_client: httpx.Client,
        stock_client: httpx.Client,
        accounting_client: httpx.Client,
    ) -> None:
        """발주→입고→재고검증→구매송장→분개검증→지급→AP 소거까지 전체 흐름."""
        # --- Step 1: 공급업체 생성 (buying 서비스) ---
        resp = buying_client.post(
            "/api/v1/suppliers",
            json={
                "supplier_name": "P2P E2E 공급업체",
                "supplier_type": "company",
                "tax_id": "222-33-44444",
                "payment_terms": "30일",
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        supplier = resp.json()
        supplier_id = supplier["_id"]

        # --- Step 2: 품목 생성 (stock 서비스) ---
        resp = stock_client.post(
            "/api/v1/items",
            json={
                "item_name": "P2P 원자재 A",
                "item_group": "원자재",
                "stock_uom": "EA",
                "is_stock_item": True,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        item = resp.json()
        item_code = item["item_code"]

        # --- Step 3: 구매주문 생성 + 제출 ---
        qty = 200
        rate = 1500
        net_total = qty * rate  # 300,000

        resp = buying_client.post(
            "/api/v1/purchase-orders",
            json={
                "supplier_id": supplier_id,
                "supplier_name": "P2P E2E 공급업체",
                "transaction_date": "2026-03-20",
                "items": [
                    {
                        "item_code": item_code,
                        "item_name": "P2P 원자재 A",
                        "qty": qty,
                        "rate": rate,
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        po = resp.json()
        po_id = po["id"]

        # 구매주문 조회 — 총액 검증
        resp = buying_client.get(
            f"/api/v1/purchase-orders/{po_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["total"] == float(net_total)

        # 구매주문 제출
        resp = buying_client.post(
            f"/api/v1/purchase-orders/{po_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # --- Step 4: 입고 생성 + 제출 (stock 서비스) ---
        resp = stock_client.post(
            "/api/v1/purchase-receipts",
            json={
                "supplier_name": "P2P E2E 공급업체",
                "posting_date": "2026-03-22",
                "purchase_order_id": po_id,
                "items": [
                    {
                        "item_code": item_code,
                        "item_name": "P2P 원자재 A",
                        "qty": qty,
                        "rate": rate,
                        "warehouse": "메인 창고",
                    },
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        pr = resp.json()
        pr_id = pr["id"]

        # 입고 제출
        resp = stock_client.post(
            f"/api/v1/purchase-receipts/{pr_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # --- 검증: StockLedgerEntry 생성 확인 ---
        def _재고원장_생성_확인():
            resp = stock_client.get(
                "/api/v1/stock-ledger-entries",
                params={"voucher_no": pr_id},
                headers=HEADERS,
            )
            data = resp.json()
            return resp.status_code == 200 and data.get("total", 0) > 0

        wait_for_condition(
            _재고원장_생성_확인,
            timeout=10.0,
            description="재고원장(StockLedgerEntry) 생성 대기",
        )
        resp = stock_client.get(
            "/api/v1/stock-ledger-entries",
            params={"voucher_no": pr_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        sle_data = resp.json()
        assert sle_data["total"] > 0, "입고 제출 후 재고원장이 생성되어야 합니다"
        sle = sle_data["data"][0]
        assert sle["actual_qty"] == qty

        # --- 검증: stock_bins 잔고 증가 확인 ---
        def _재고빈_잔고_확인():
            resp = stock_client.get(
                "/api/v1/stock-bins",
                params={"item_code": item_code, "warehouse": "메인 창고"},
                headers=HEADERS,
            )
            data = resp.json()
            return resp.status_code == 200 and data.get("total", 0) > 0

        wait_for_condition(
            _재고빈_잔고_확인,
            timeout=10.0,
            description="재고빈 잔고 반영 대기",
        )
        resp = stock_client.get(
            "/api/v1/stock-bins",
            params={"item_code": item_code, "warehouse": "메인 창고"},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        bin_data = resp.json()
        assert bin_data["total"] > 0, "입고 후 재고빈 레코드가 존재해야 합니다"
        stock_bin = bin_data["data"][0]
        assert stock_bin["actual_qty"] >= qty

        # --- Step 5: 구매송장 생성 + 제출 ---
        tax_amount = float(net_total) * 0.1  # 부가세 10%
        grand_total = float(net_total) + tax_amount  # 330,000

        resp = buying_client.post(
            "/api/v1/purchase-invoices",
            json={
                "supplier_id": supplier_id,
                "supplier_name": "P2P E2E 공급업체",
                "posting_date": "2026-03-23",
                "due_date": "2026-04-23",
                "purchase_order_id": po_id,
                "purchase_receipt_id": pr_id,
                "items": [
                    {
                        "item_code": item_code,
                        "item_name": "P2P 원자재 A",
                        "qty": qty,
                        "rate": rate,
                    },
                ],
                "taxes": [
                    {"tax_type": "부가세", "rate": 10, "amount": tax_amount},
                ],
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        pi = resp.json()
        pi_id = pi["id"]

        # 구매송장 조회 — grand_total 검증
        resp = buying_client.get(
            f"/api/v1/purchase-invoices/{pi_id}",
            headers=HEADERS,
        )
        assert resp.status_code == 200
        assert resp.json()["grand_total"] == grand_total

        # 구매송장 제출
        resp = buying_client.post(
            f"/api/v1/purchase-invoices/{pi_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # --- 검증: 분개전표(매입) 자동 생성 확인 ---
        def _매입_분개전표_생성_확인():
            resp = accounting_client.get(
                "/api/v1/journal-entries",
                params={"voucher_no": pi_id},
                headers=HEADERS,
            )
            data = resp.json()
            return resp.status_code == 200 and data.get("total", 0) > 0

        wait_for_condition(
            _매입_분개전표_생성_확인,
            timeout=10.0,
            description="매입 분개전표 자동생성 대기",
        )
        resp = accounting_client.get(
            "/api/v1/journal-entries",
            params={"voucher_no": pi_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        je_data = resp.json()
        assert je_data["total"] > 0, "구매송장 제출 후 분개전표가 자동 생성되어야 합니다"
        je = je_data["data"][0]
        # 차대변 합계 일치 검증
        assert je["total_debit"] == je["total_credit"]

        # --- 검증: AP(매입채무) 생성 확인 ---
        def _매입채무_생성_확인():
            resp = accounting_client.get(
                "/api/v1/accounts-payable",
                params={"voucher_no": pi_id},
                headers=HEADERS,
            )
            data = resp.json()
            return resp.status_code == 200 and data.get("total", 0) > 0

        wait_for_condition(
            _매입채무_생성_확인,
            timeout=10.0,
            description="매입채무(AP) 생성 대기",
        )
        resp = accounting_client.get(
            "/api/v1/accounts-payable",
            params={"voucher_no": pi_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        ap_data = resp.json()
        assert ap_data["total"] > 0, "구매송장 제출 후 매입채무가 생성되어야 합니다"
        ap = ap_data["data"][0]
        assert ap["outstanding_amount"] == grand_total

        # --- Step 6: 지급 생성 + 제출 ---
        resp = accounting_client.post(
            "/api/v1/payment-entries",
            json={
                "payment_type": "pay",
                "party_type": "supplier",
                "party_id": supplier_id,
                "party_name": "P2P E2E 공급업체",
                "posting_date": "2026-03-25",
                "paid_amount": grand_total,
                "received_amount": grand_total,
                "reference_doctype": "purchase_invoice",
                "reference_name": pi_id,
            },
            headers=HEADERS,
        )
        assert resp.status_code == 201
        pe_id = resp.json()["_id"]

        # 지급 제출
        resp = accounting_client.post(
            f"/api/v1/payment-entries/{pe_id}/submit",
            headers=HEADERS,
        )
        assert resp.status_code == 200

        # --- 검증: AP outstanding_amount == 0 ---
        def _매입채무_소거_확인():
            resp = accounting_client.get(
                "/api/v1/accounts-payable",
                params={"voucher_no": pi_id},
                headers=HEADERS,
            )
            if resp.status_code != 200:
                return False
            data = resp.json()
            if data.get("total", 0) <= 0:
                return False
            return data["data"][0].get("outstanding_amount") == 0

        wait_for_condition(
            _매입채무_소거_확인,
            timeout=10.0,
            description="매입채무(AP) 소거 대기",
        )
        resp = accounting_client.get(
            "/api/v1/accounts-payable",
            params={"voucher_no": pi_id},
            headers=HEADERS,
        )
        assert resp.status_code == 200
        ap_data = resp.json()
        assert ap_data["total"] > 0, "지급 후에도 매입채무 레코드가 존재해야 합니다"
        ap = ap_data["data"][0]
        assert ap["outstanding_amount"] == 0, "지급 후 매입채무 잔액이 0이어야 합니다"
