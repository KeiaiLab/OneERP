"""채번규칙(NamingSeries) 시드 — 주요 엔티티별 넘버링 프리픽스.

패턴: {prefix}-{YYYY}-{#####} (예: SO-2026-00001)
"""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.config import get_core_settings
from oneerp_core.db import get_client

logger = logging.getLogger(__name__)

SERIES: list[dict[str, Any]] = [
    # 판매
    {"prefix": "SO", "entity": "sales_orders", "description": "판매주문"},
    {"prefix": "QTN", "entity": "quotations", "description": "견적서"},
    {"prefix": "DN", "entity": "delivery_notes", "description": "납품서"},
    {"prefix": "INV", "entity": "sales_invoices", "description": "매출전표"},
    {"prefix": "SR", "entity": "sales_returns", "description": "판매반품"},
    # 구매
    {"prefix": "PO", "entity": "purchase_orders", "description": "구매주문"},
    {"prefix": "PINV", "entity": "purchase_invoices", "description": "매입전표"},
    {"prefix": "PR", "entity": "purchase_receipts", "description": "입고전표"},
    {"prefix": "RFQ", "entity": "request_for_quotations", "description": "견적요청"},
    # 회계
    {"prefix": "JE", "entity": "journal_entries", "description": "분개"},
    {"prefix": "PE", "entity": "payment_entries", "description": "결제"},
    {"prefix": "BR", "entity": "bank_reconciliations", "description": "은행대사"},
    {"prefix": "ETAX", "entity": "etax_invoices", "description": "전자세금계산서"},
    # 재고
    {"prefix": "STE", "entity": "stock_entries", "description": "재고이동"},
    {"prefix": "MR", "entity": "material_requests", "description": "자재요청"},
    {"prefix": "SREC", "entity": "stock_reconciliations", "description": "재고조정"},
    # 경비
    {"prefix": "EXP", "entity": "expense_claims", "description": "경비청구"},
    # 인사/급여
    {"prefix": "EMP", "entity": "employees", "description": "직원"},
    {"prefix": "LA", "entity": "leave_applications", "description": "휴가신청"},
    {"prefix": "ATT", "entity": "attendances", "description": "근태"},
    {"prefix": "SS", "entity": "salary_slips", "description": "급여명세"},
    {"prefix": "PRL", "entity": "payroll_entries", "description": "급여계산"},
    # 생산
    {"prefix": "WO", "entity": "work_orders", "description": "작업지시"},
    {"prefix": "JC", "entity": "job_cards", "description": "작업카드"},
    {"prefix": "BOM", "entity": "boms", "description": "자재명세서"},
    # 기타
    {"prefix": "PROJ", "entity": "projects", "description": "프로젝트"},
    {"prefix": "TASK", "entity": "tasks", "description": "작업"},
    {"prefix": "ISS", "entity": "issues", "description": "이슈"},
]


def seed(tenant_id: str = "default") -> int:
    """채번규칙을 시드한다. 이미 존재하면 건너뛴다.

    Returns:
        새로 삽입한 채번규칙 수.
    """
    settings = get_core_settings()
    client = get_client()
    db = client[settings.database_name]
    collection = db["naming_series"]

    count = 0
    for series in SERIES:
        existing = collection.find_one(
            {"prefix": series["prefix"], "tenant_id": tenant_id},
        )
        if existing:
            continue

        doc = {
            "_id": f"NSRS-{series['prefix']}",
            "tenant_id": tenant_id,
            "prefix": series["prefix"],
            "current_value": 0,
            "description": series["description"],
            "docstatus": 0,
        }
        collection.insert_one(doc)
        count += 1

    logger.info("채번규칙 시드 완료: %d개 삽입", count)
    return count
