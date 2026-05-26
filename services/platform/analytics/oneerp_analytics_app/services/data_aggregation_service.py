"""데이터 집계 서비스 — 매출, 재고, 매출채권 집계 및 KPI 일괄 수집."""

from __future__ import annotations

import logging
from typing import Any

from oneerp_core.repository import Repository

logger = logging.getLogger(__name__)


class DataAggregationService:
    """데이터 집계 비즈니스 로직."""

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._invoice_repo = Repository("sales_invoices", tenant_id=tenant_id)
        self._stock_repo = Repository("stock_ledger_entries", tenant_id=tenant_id)
        self._ar_repo = Repository("accounts_receivable", tenant_id=tenant_id)

    def aggregate_revenue(self, period: str) -> dict[str, Any]:
        """sales_invoices에서 기간별 매출을 합산한다."""
        invoices = self._invoice_repo.find_many({"period": period}, limit=1000)
        total = sum(inv.get("grand_total", 0.0) for inv in invoices)
        logger.info("매출 집계: 기간=%s, 총액=%.2f, 건수=%d", period, total, len(invoices))
        return {"period": period, "revenue": total, "invoice_count": len(invoices)}

    def aggregate_inventory_value(self) -> dict[str, Any]:
        """재고 수량 x 가격을 합산한다."""
        entries = self._stock_repo.find_many(limit=1000)
        total = sum(e.get("qty", 0.0) * e.get("valuation_rate", 0.0) for e in entries)
        logger.info("재고 가치 집계: 총액=%.2f, 항목=%d건", total, len(entries))
        return {"inventory_value": total, "entry_count": len(entries)}

    def aggregate_receivables(self) -> dict[str, Any]:
        """매출채권(AR) 미수금을 합산한다."""
        receivables = self._ar_repo.find_many(limit=1000)
        total = sum(r.get("outstanding_amount", 0.0) for r in receivables)
        logger.info("매출채권 집계: 총액=%.2f, 건수=%d", total, len(receivables))
        return {"receivables": total, "count": len(receivables)}

    def collect_all_kpis(self, period: str) -> dict[str, Any]:
        """4개 핵심 지표를 일괄 수집한다."""
        revenue = self.aggregate_revenue(period)
        inventory = self.aggregate_inventory_value()
        receivables = self.aggregate_receivables()

        return {
            "period": period,
            "revenue": revenue["revenue"],
            "inventory_value": inventory["inventory_value"],
            "receivables": receivables["receivables"],
        }
