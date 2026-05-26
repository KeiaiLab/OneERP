"""Order-to-Cash 플로우 단계 헬퍼 — 재사용 가능한 비즈니스 단계 함수들.

각 함수는 단일 책임으로 분리되어 있어, 다른 플로우(반품/취소 등)에서도 재사용 가능하다.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import httpx


def wait_until(
    check: Callable[[], Any],
    *,
    timeout: float = 10.0,
    interval: float = 0.5,
    description: str = "조건 충족 대기",
) -> Any:
    """조건이 truthy가 될 때까지 폴링 — 성공 시 반환값을 그대로 돌려준다."""
    deadline = time.monotonic() + timeout
    last_err: Exception | None = None
    while time.monotonic() < deadline:
        try:
            result = check()
            if result:
                return result
        except Exception as exc:
            last_err = exc
        time.sleep(interval)
    msg = f"{description}: {timeout}초 내 조건 미충족"
    if last_err is not None:
        msg += f" (마지막 에러: {last_err})"
    raise TimeoutError(msg)


def _post(client: httpx.Client, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    resp = client.post(path, json=payload)
    assert resp.status_code == 201, f"POST {path} 실패: {resp.status_code} {resp.text}"
    return resp.json()


def _submit(client: httpx.Client, path: str) -> dict[str, Any]:
    resp = client.post(path)
    assert resp.status_code == 200, f"SUBMIT {path} 실패: {resp.status_code} {resp.text}"
    return resp.json()


def _doc_id(doc: dict[str, Any]) -> str:
    return str(doc.get("_id") or doc.get("id") or "")


def create_customer(selling: httpx.Client, *, name: str, tax_id: str) -> str:
    """고객을 생성하고 id를 반환한다."""
    doc = _post(
        selling,
        "/api/v1/customers",
        {"customer_name": name, "customer_type": "company", "tax_id": tax_id},
    )
    return _doc_id(doc)


def create_item(stock: httpx.Client, *, name: str) -> str:
    """재고 품목을 생성하고 item_code를 반환한다."""
    doc = _post(
        stock,
        "/api/v1/items",
        {
            "item_name": name,
            "item_group": "완제품",
            "stock_uom": "EA",
            "is_stock_item": True,
        },
    )
    return str(doc["item_code"])


def receive_stock(
    stock: httpx.Client,
    *,
    item_code: str,
    item_name: str,
    qty: int,
    rate: int,
    warehouse: str = "메인 창고",
    posting_date: str,
) -> str:
    """입고를 생성 후 제출하고 purchase_receipt id를 반환한다."""
    doc = _post(
        stock,
        "/api/v1/purchase-receipts",
        {
            "supplier_name": "E2E 입고 공급사",
            "posting_date": posting_date,
            "items": [
                {
                    "item_code": item_code,
                    "item_name": item_name,
                    "qty": qty,
                    "rate": rate,
                    "warehouse": warehouse,
                },
            ],
        },
    )
    pr_id = _doc_id(doc)
    _submit(stock, f"/api/v1/purchase-receipts/{pr_id}/submit")
    return pr_id


def create_sales_order(
    selling: httpx.Client,
    *,
    customer_id: str,
    customer_name: str,
    item_code: str,
    item_name: str,
    qty: int,
    rate: int,
    transaction_date: str,
    delivery_date: str,
) -> str:
    """판매주문 생성 → 제출 후 id 반환."""
    doc = _post(
        selling,
        "/api/v1/sales-orders",
        {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "transaction_date": transaction_date,
            "delivery_date": delivery_date,
            "items": [
                {
                    "item_code": item_code,
                    "item_name": item_name,
                    "qty": qty,
                    "rate": rate,
                },
            ],
        },
    )
    so_id = _doc_id(doc)
    _submit(selling, f"/api/v1/sales-orders/{so_id}/submit")
    return so_id


def create_delivery_note(
    selling: httpx.Client,
    *,
    customer_id: str,
    customer_name: str,
    sales_order_id: str,
    item_code: str,
    item_name: str,
    qty: int,
    posting_date: str,
    warehouse: str = "메인 창고",
) -> str:
    """납품서 생성 → 제출 후 id 반환."""
    doc = _post(
        selling,
        "/api/v1/delivery-notes",
        {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "posting_date": posting_date,
            "sales_order_id": sales_order_id,
            "items": [
                {
                    "item_code": item_code,
                    "item_name": item_name,
                    "qty": qty,
                    "warehouse": warehouse,
                },
            ],
        },
    )
    dn_id = _doc_id(doc)
    _submit(selling, f"/api/v1/delivery-notes/{dn_id}/submit")
    return dn_id


def issue_sales_invoice(
    selling: httpx.Client,
    *,
    customer_id: str,
    customer_name: str,
    sales_order_id: str,
    delivery_note_id: str,
    item_code: str,
    item_name: str,
    qty: int,
    rate: int,
    tax_rate_pct: int,
    posting_date: str,
    due_date: str,
) -> dict[str, Any]:
    """매출송장 생성 → 제출 후 {id, grand_total} 반환."""
    net_total = qty * rate
    tax_amount = net_total * tax_rate_pct // 100
    grand_total = net_total + tax_amount
    doc = _post(
        selling,
        "/api/v1/sales-invoices",
        {
            "customer_id": customer_id,
            "customer_name": customer_name,
            "posting_date": posting_date,
            "due_date": due_date,
            "sales_order_id": sales_order_id,
            "delivery_note_id": delivery_note_id,
            "items": [
                {
                    "item_code": item_code,
                    "item_name": item_name,
                    "qty": qty,
                    "rate": rate,
                },
            ],
            "taxes": [
                {"tax_type": "부가세", "rate": tax_rate_pct, "amount": tax_amount},
            ],
        },
    )
    sinv_id = str(doc["id"])
    _submit(selling, f"/api/v1/sales-invoices/{sinv_id}/submit")
    return {"id": sinv_id, "grand_total": float(grand_total)}


def assert_journal_entry_created(accounting: httpx.Client, *, voucher_no: str) -> dict[str, Any]:
    """매출송장에 대한 분개전표 자동 생성을 기다려 검증한다."""

    def _check() -> dict[str, Any] | None:
        resp = accounting.get("/api/v1/journal-entries", params={"voucher_no": voucher_no})
        if resp.status_code != 200:
            return None
        body = resp.json()
        if body.get("total", 0) > 0:
            return body
        return None

    body = wait_until(_check, timeout=10.0, description=f"분개전표 자동생성({voucher_no})")
    entry = body["data"][0]
    assert entry["total_debit"] == entry["total_credit"], "차변/대변 불일치"
    return entry


def assert_ar_outstanding(
    accounting: httpx.Client,
    *,
    voucher_no: str,
    expected_outstanding: float,
) -> dict[str, Any]:
    """AR outstanding_amount가 기대값에 도달할 때까지 대기 후 검증한다."""

    def _check() -> dict[str, Any] | None:
        resp = accounting.get(
            "/api/v1/accounts-receivable",
            params={"voucher_no": voucher_no},
        )
        if resp.status_code != 200:
            return None
        body = resp.json()
        if body.get("total", 0) <= 0:
            return None
        if body["data"][0].get("outstanding_amount") == expected_outstanding:
            return body
        return None

    body = wait_until(
        _check,
        timeout=10.0,
        description=f"AR outstanding=={expected_outstanding}({voucher_no})",
    )
    return body["data"][0]


def settle_payment(
    accounting: httpx.Client,
    *,
    customer_id: str,
    customer_name: str,
    sales_invoice_id: str,
    amount: float,
    posting_date: str,
) -> str:
    """수금(Payment Entry) 생성 → 제출 후 id 반환."""
    doc = _post(
        accounting,
        "/api/v1/payment-entries",
        {
            "payment_type": "receive",
            "party_type": "customer",
            "party_id": customer_id,
            "party_name": customer_name,
            "posting_date": posting_date,
            "paid_amount": amount,
            "received_amount": amount,
            "reference_doctype": "sales_invoice",
            "reference_name": sales_invoice_id,
        },
    )
    pe_id = _doc_id(doc)
    _submit(accounting, f"/api/v1/payment-entries/{pe_id}/submit")
    return pe_id
