"""매출채권(Accounts Receivable) 리포트 모델 — 집계 뷰, 읽기 전용."""

from __future__ import annotations

from datetime import date  # noqa: TC003
from decimal import Decimal

from oneerp_core.document import BaseDocument


class AccountsReceivable(BaseDocument):
    """매출채권 리포트 문서 — 미수금 현황 집계.

    naming prefix: AREC
    """

    customer: str = ""
    outstanding_amount: Decimal = Decimal(0)
    due_date: date | None = None
    aging_bucket: str = ""
    invoice_id: str = ""
