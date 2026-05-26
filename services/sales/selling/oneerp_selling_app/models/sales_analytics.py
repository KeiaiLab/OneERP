"""판매 분석(SalesAnalytics) 리포트 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument


class SalesAnalytics(BaseDocument):
    """판매 분석 리포트 — 읽기 전용 집계 뷰.

    naming prefix: SANA
    """

    period: str = ""
    item_code: str = ""
    customer: str = ""
    total_qty: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)
