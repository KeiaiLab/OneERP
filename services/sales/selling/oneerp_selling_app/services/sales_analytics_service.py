"""판매 분석 서비스 — Route Repository 의존성 은닉 레이어.

M3 arch-baseline 감소: Route 에서 Repository 직접 인스턴스화 제거.
집계/랭킹 계산 로직은 현행 유지하고, 데이터 로드만 Service 로 격리.
"""

from __future__ import annotations

from typing import Any

from oneerp_core.repository import Repository


class SalesAnalyticsService:
    """판매 분석 집계용 데이터 로더.

    Route 단의 `_get_invoice_repo` / `_get_quotation_repo` 팩토리를 대체한다.
    집계·랭킹 로직은 Route 의 private helper 로 남겨 diff 최소화.
    """

    def __init__(self, tenant_id: str) -> None:
        self._tenant_id = tenant_id
        self._invoice_repo = Repository("sales_invoices", tenant_id=tenant_id)
        self._quotation_repo = Repository("quotations", tenant_id=tenant_id)

    def load_invoices(self) -> list[dict[str, Any]]:
        """판매송장 최근순 5000건을 반환한다."""
        return self._invoice_repo.find_many(limit=5000, sort=[("posting_date", -1)])

    def load_quotations(self) -> list[dict[str, Any]]:
        """견적 최근순 5000건을 반환한다."""
        return self._quotation_repo.find_many(limit=5000, sort=[("transaction_date", -1)])
