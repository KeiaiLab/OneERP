"""E2E 어설션 헬퍼 — 문서 상태, 분개, 재고 검증."""

from __future__ import annotations

from typing import Any

import httpx

from .api_client import HEADERS, list_docs


def assert_doc_status(doc: dict[str, Any], expected_status: int) -> None:
    """문서의 docstatus가 기대값인지 확인한다. (0=DRAFT, 1=SUBMITTED, 2=CANCELLED)"""
    actual = doc.get("docstatus")
    assert actual == expected_status, (
        f"docstatus 불일치: expected={expected_status}, actual={actual}, doc_id={doc.get('_id')}"
    )


def assert_journal_created(
    accounting_client: httpx.Client,
    reference_id: str,
    *,
    min_entries: int = 2,
) -> dict[str, Any]:
    """참조 문서에 대한 분개가 생성되었는지 + 차대변 균형을 확인한다."""
    journals = list_docs(accounting_client, "journal-entries", reference_doc_id=reference_id)
    assert len(journals) > 0, f"분개 미생성: reference={reference_id}"

    journal = journals[0]
    entries = journal.get("entries", journal.get("items", []))
    assert len(entries) >= min_entries, (
        f"분개 항목 부족: expected>={min_entries}, actual={len(entries)}"
    )

    total_debit = sum(float(e.get("debit", 0)) for e in entries)
    total_credit = sum(float(e.get("credit", 0)) for e in entries)
    assert abs(total_debit - total_credit) < 0.01, (
        f"차대변 불균형: debit={total_debit}, credit={total_credit}"
    )
    return journal


def assert_stock_balance(
    stock_client: httpx.Client,
    item_code: str,
    warehouse: str,
    *,
    expected_qty: float | None = None,
    expected_rate: float | None = None,
) -> dict[str, Any]:
    """품목의 재고 잔량/평가 단가를 확인한다."""
    resp = stock_client.get(
        "/api/v1/stock-balances",
        params={"item_code": item_code, "warehouse": warehouse},
        headers=HEADERS,
    )
    assert resp.status_code == 200, f"재고 조회 실패: {resp.status_code}"
    body = resp.json()
    data = body.get("data", [body]) if isinstance(body, dict) else body
    assert len(data) > 0, f"재고 데이터 없음: item={item_code}, warehouse={warehouse}"

    balance = data[0]
    if expected_qty is not None:
        actual_qty = float(balance.get("actual_qty", balance.get("qty", 0)))
        assert abs(actual_qty - expected_qty) < 0.01, (
            f"재고 수량 불일치: expected={expected_qty}, actual={actual_qty}"
        )
    if expected_rate is not None:
        actual_rate = float(balance.get("valuation_rate", balance.get("rate", 0)))
        assert abs(actual_rate - expected_rate) < 0.01, (
            f"평가단가 불일치: expected={expected_rate}, actual={actual_rate}"
        )
    return balance
