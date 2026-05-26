"""역할 및 기본 권한 시드 — 시스템 내장 역할.

각 모듈별 기본 역할과 권한을 시드한다.
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.config import get_core_settings
from oneerp_core.db import get_client

logger = logging.getLogger(__name__)

ROLES: list[dict[str, Any]] = [
    {
        "name": "System Manager",
        "description": "시스템 전체 관리자 — 모든 권한 보유",
        "is_system": True,
        "scope": "platform",
    },
    {
        "name": "Accounts Manager",
        "description": "회계 관리자 — 계정, 분개, 결산 전체 관리",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Accounts User",
        "description": "회계 담당자 — 분개 작성 및 조회",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Sales Manager",
        "description": "영업 관리자 — 판매 전체 관리",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Sales User",
        "description": "영업 담당자 — 견적/주문/납품 처리",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Purchase Manager",
        "description": "구매 관리자 — 구매 전체 관리",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Purchase User",
        "description": "구매 담당자 — 발주/입고 처리",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Stock Manager",
        "description": "재고 관리자 — 창고/재고 전체 관리",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Stock User",
        "description": "재고 담당자 — 입출고 처리",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "HR Manager",
        "description": "인사 관리자 — 인사/근태 전체 관리",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "HR User",
        "description": "인사 담당자 — 근태/휴가 처리",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Payroll Manager",
        "description": "급여 관리자 — 급여 계산 및 지급 관리",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Payroll User",
        "description": "급여 담당자 — 급여명세 조회",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Expense User",
        "description": "경비 담당자 — 경비 청구 및 조회",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Manufacturing User",
        "description": "생산 담당자 — 작업지시/BOM 관리",
        "is_system": True,
        "scope": "tenant",
    },
    {
        "name": "Quality Manager",
        "description": "품질 관리자 — 품질 검사 및 관리",
        "is_system": True,
        "scope": "tenant",
    },
]

# 역할별 기본 권한 매핑 (doctype → 권한)
ROLE_PERMISSIONS: dict[str, list[dict[str, Any]]] = {
    "System Manager": [
        {
            "doctype": "*",
            "module": "*",
            "read": True,
            "write": True,
            "create": True,
            "delete": True,
            "submit": True,
            "cancel": True,
            "export": True,
            "report": True,
        },
    ],
    "Accounts Manager": [
        {
            "doctype": "account",
            "module": "accounting",
            "read": True,
            "write": True,
            "create": True,
            "delete": True,
            "submit": True,
            "cancel": True,
            "export": True,
            "report": True,
        },
        {
            "doctype": "journal_entry",
            "module": "accounting",
            "read": True,
            "write": True,
            "create": True,
            "delete": True,
            "submit": True,
            "cancel": True,
            "export": True,
            "report": True,
        },
        {
            "doctype": "payment_entry",
            "module": "accounting",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
            "cancel": True,
            "export": True,
            "report": True,
        },
        {
            "doctype": "sales_invoice",
            "module": "selling",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
            "cancel": True,
            "export": True,
            "report": True,
        },
        {
            "doctype": "purchase_invoice",
            "module": "buying",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
            "cancel": True,
            "export": True,
            "report": True,
        },
    ],
    "Sales User": [
        {"doctype": "customer", "module": "selling", "read": True, "write": True, "create": True},
        {
            "doctype": "quotation",
            "module": "selling",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
        },
        {
            "doctype": "sales_order",
            "module": "selling",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
        },
        {
            "doctype": "delivery_note",
            "module": "selling",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
        },
        {"doctype": "sales_invoice", "module": "selling", "read": True},
    ],
    "Purchase User": [
        {"doctype": "supplier", "module": "buying", "read": True, "write": True, "create": True},
        {
            "doctype": "purchase_order",
            "module": "buying",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
        },
        {
            "doctype": "purchase_receipt",
            "module": "buying",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
        },
        {"doctype": "purchase_invoice", "module": "buying", "read": True},
    ],
    "Stock User": [
        {"doctype": "item", "module": "stock", "read": True, "write": True, "create": True},
        {
            "doctype": "stock_entry",
            "module": "stock",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
        },
        {"doctype": "warehouse", "module": "stock", "read": True},
        {
            "doctype": "stock_reconciliation",
            "module": "stock",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
        },
    ],
    "HR Manager": [
        {
            "doctype": "employee",
            "module": "hr",
            "read": True,
            "write": True,
            "create": True,
            "delete": True,
            "export": True,
            "report": True,
        },
        {
            "doctype": "attendance",
            "module": "hr",
            "read": True,
            "write": True,
            "create": True,
            "export": True,
            "report": True,
        },
        {
            "doctype": "leave_application",
            "module": "hr",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
            "cancel": True,
        },
    ],
    "Expense User": [
        {
            "doctype": "expense_claim",
            "module": "expenses",
            "read": True,
            "write": True,
            "create": True,
            "submit": True,
        },
        {"doctype": "expense_type", "module": "expenses", "read": True},
    ],
}


def seed(tenant_id: str = "default") -> int:
    """역할과 기본 권한을 시드한다. 이미 존재하면 건너뛴다.

    Returns:
        새로 삽입한 역할 수.
    """
    settings = get_core_settings()
    client = get_client()
    db = client[settings.database_name]
    roles_col = db["roles"]
    perms_col = db["role_permissions"]

    role_count = 0
    perm_count = 0

    for role in ROLES:
        existing = roles_col.find_one(
            {"role_name": role["name"], "tenant_id": tenant_id},
        )
        if existing:
            continue

        role_id = f"ROL-{role['name'].upper().replace(' ', '-')}"
        roles_col.insert_one(
            {
                "_id": role_id,
                "tenant_id": tenant_id,
                "role_name": role["name"],
                "description": role["description"],
                "is_custom": False,
                "is_system": role["is_system"],
                "scope": role["scope"],
                "docstatus": 0,
            }
        )
        role_count += 1

        # 해당 역할의 기본 권한 시드
        perms = ROLE_PERMISSIONS.get(role["name"], [])
        for idx, perm in enumerate(perms):
            perm_id = f"RPERM-{role['name'].upper().replace(' ', '-')}-{idx:03d}"
            existing_perm = perms_col.find_one(
                {"_id": perm_id, "tenant_id": tenant_id},
            )
            if existing_perm:
                continue

            perms_col.insert_one(
                {
                    "_id": perm_id,
                    "tenant_id": tenant_id,
                    "role": role["name"],
                    "doctype": perm["doctype"],
                    "module": perm.get("module", ""),
                    "read": perm.get("read", True),
                    "write": perm.get("write", False),
                    "create": perm.get("create", False),
                    "delete": perm.get("delete", False),
                    "submit": perm.get("submit", False),
                    "cancel": perm.get("cancel", False),
                    "export": perm.get("export", False),
                    "report": perm.get("report", False),
                    "docstatus": 0,
                }
            )
            perm_count += 1

    logger.info("역할 시드 완료: %d개 역할, %d개 권한 삽입", role_count, perm_count)
    return role_count
