"""은행대사(Bank Reconciliation) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class BankReconciliationCreate(BaseModel):
    """은행대사 생성 요청 스키마."""

    bank_account: str
    from_date: date | None = None
    to_date: date | None = None
    bank_balance: Decimal = Decimal(0)
    system_balance: Decimal = Decimal(0)
    difference: Decimal = Decimal(0)


class BankReconciliationUpdate(BaseModel):
    """은행대사 수정 요청 스키마."""

    bank_account: str | None = None
    from_date: date | None = None
    to_date: date | None = None
    bank_balance: Decimal | None = None
    system_balance: Decimal | None = None
    difference: Decimal | None = None


class BankReconciliation(BaseDocument):
    """은행대사 문서 — 은행 잔액과 시스템 잔액 대사.

    naming prefix: BR
    """

    bank_account: str = ""
    from_date: date | None = None
    to_date: date | None = None
    bank_balance: Decimal = Decimal(0)
    system_balance: Decimal = Decimal(0)
    difference: Decimal = Decimal(0)
