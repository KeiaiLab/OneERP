"""은행 거래(BankTransaction) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class BankTransactionStatus(StrEnum):
    """은행 거래 상태."""

    UNRECONCILED = "unreconciled"
    RECONCILED = "reconciled"
    CANCELLED = "cancelled"


class BankTransactionCreate(BaseModel):
    """은행 거래 생성 요청 스키마."""

    bank_account_id: str
    transaction_date: date | None = None
    amount: Decimal = Decimal(0)
    transaction_type: str = ""
    description: str = ""
    reference: str = ""
    is_reconciled: bool = False


class BankTransactionUpdate(BaseModel):
    """은행 거래 수정 요청 스키마."""

    bank_account_id: str | None = None
    transaction_date: date | None = None
    amount: Decimal | None = None
    transaction_type: str | None = None
    description: str | None = None
    reference: str | None = None
    is_reconciled: bool | None = None


class BankTransaction(BaseDocument):
    """은행 거래 문서."""

    status: BankTransactionStatus = Field(
        default=BankTransactionStatus.UNRECONCILED,
        description="은행 거래 상태",
    )
    bank_account_id: str = ""
    transaction_date: date | None = None
    amount: Decimal = Decimal(0)
    transaction_type: str = ""
    description: str = ""
    reference: str = ""
    is_reconciled: bool = False
