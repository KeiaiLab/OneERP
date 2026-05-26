"""수금대사(Payment Reconciliation) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class PaymentReconciliationCreate(BaseModel):
    """수금대사 생성 요청 스키마."""

    party_type: str
    party: str
    receivable_payable_account: str
    from_date: date | None = None
    to_date: date | None = None


class PaymentReconciliationUpdate(BaseModel):
    """수금대사 수정 요청 스키마."""

    party_type: str | None = None
    party: str | None = None
    receivable_payable_account: str | None = None
    from_date: date | None = None
    to_date: date | None = None


class PaymentReconciliation(BaseDocument):
    """수금대사 문서 — 수금/지급 대사 처리.

    naming prefix: PREC
    """

    party_type: str = ""
    party: str = ""
    receivable_payable_account: str = ""
    from_date: date | None = None
    to_date: date | None = None
