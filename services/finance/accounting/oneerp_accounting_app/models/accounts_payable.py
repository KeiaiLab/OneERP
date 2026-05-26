"""매입채무(Accounts Payable) 리포트 모델 — 집계 뷰, 읽기 전용."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class AccountsPayableCreate(BaseModel):
    """매입채무 리포트 생성 요청 스키마."""

    supplier: str
    supplier_name: str = ""
    outstanding_amount: Decimal = Decimal(0)
    due_date: date | None = None
    aging_bucket: str = ""
    invoice_id: str = ""


class AccountsPayableUpdate(BaseModel):
    """매입채무 리포트 수정 요청 스키마."""

    supplier: str | None = None
    supplier_name: str | None = None
    outstanding_amount: Decimal | None = None
    due_date: date | None = None
    aging_bucket: str | None = None
    invoice_id: str | None = None


class AccountsPayable(BaseDocument):
    """매입채무 리포트 문서 — 미지급금 현황 집계.

    naming prefix: AP
    """

    supplier: str = ""
    supplier_name: str = ""
    outstanding_amount: Decimal = Decimal(0)
    due_date: date | None = None
    aging_bucket: str = ""
    invoice_id: str = ""
