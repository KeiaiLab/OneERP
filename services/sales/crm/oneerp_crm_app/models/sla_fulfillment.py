"""SLA이행현황(SLAFulfillment) 문서 모델 — Support 모듈 (Report)."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument


class SLAFulfillment(BaseDocument):
    """SLA이행현황 — Support SLA 이행 집계 뷰."""

    sla: str = ""
    total_issues: int = 0
    fulfilled: int = 0
    breached: int = 0
    fulfillment_rate: Decimal = Decimal(0)
