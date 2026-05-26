"""영업파이프라인(SalesPipeline) 문서 모델 — CRM 모듈 (Report)."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument


class SalesPipeline(BaseDocument):
    """영업파이프라인 — CRM 영업파이프라인 집계 뷰."""

    stage: str = ""
    deal_count: int = 0
    total_value: Decimal = Decimal(0)
    period: str = ""
