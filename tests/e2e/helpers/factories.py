"""E2E 테스트 데이터 팩토리 — 최소 필수 필드만 포함하는 생성 데이터."""

from __future__ import annotations

from datetime import date
from typing import Any


def make_customer(
    *, name: str = "테스트 고객", customer_group: str = "일반", **overrides: Any
) -> dict[str, Any]:
    return {
        "customer_name": name,
        "customer_group": customer_group,
        "territory": "한국",
        **overrides,
    }


def make_supplier(
    *, name: str = "테스트 공급업체", supplier_group: str = "일반", **overrides: Any
) -> dict[str, Any]:
    return {"supplier_name": name, "supplier_group": supplier_group, "country": "KR", **overrides}


def make_item(
    *,
    item_code: str = "ITEM-001",
    item_name: str = "테스트 품목",
    item_group: str = "일반",
    **overrides: Any,
) -> dict[str, Any]:
    return {
        "item_code": item_code,
        "item_name": item_name,
        "item_group": item_group,
        "stock_uom": "EA",
        "is_stock_item": True,
        **overrides,
    }


def make_warehouse(
    *, name: str = "테스트 창고", warehouse_type: str = "warehouse", **overrides: Any
) -> dict[str, Any]:
    return {"name": name, "warehouse_type": warehouse_type, **overrides}


def make_account(
    *, account_name: str = "테스트 계정", account_type: str = "income", **overrides: Any
) -> dict[str, Any]:
    return {
        "account_name": account_name,
        "account_type": account_type,
        "is_group": False,
        **overrides,
    }


def make_employee(
    *,
    employee_name: str = "테스트 직원",
    department: str = "개발팀",
    designation: str = "사원",
    **overrides: Any,
) -> dict[str, Any]:
    return {
        "employee_name": employee_name,
        "department": department,
        "designation": designation,
        "date_of_joining": str(date(2025, 1, 1)),
        "date_of_birth": str(date(1990, 1, 1)),
        "gender": "남성",
        **overrides,
    }


def make_sales_order_items(
    items: list[tuple[str, int, float]] | None = None,
) -> list[dict[str, Any]]:
    """판매주문 라인아이템. items: [(item_code, qty, rate), ...]"""
    if items is None:
        items = [("ITEM-001", 10, 1200.0)]
    return [
        {
            "idx": idx,
            "item_code": code,
            "item_name": code,
            "qty": qty,
            "rate": rate,
            "amount": round(qty * rate, 2),
        }
        for idx, (code, qty, rate) in enumerate(items, start=1)
    ]
