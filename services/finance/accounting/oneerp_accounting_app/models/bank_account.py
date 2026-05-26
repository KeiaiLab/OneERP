"""은행 계좌(BankAccount) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class BankAccountCreate(BaseModel):
    """은행 계좌 생성 요청 스키마."""

    account_name: str
    bank_name: str
    account_number: str
    currency: str = "KRW"
    balance: Decimal = Decimal(0)
    is_active: bool = True


class BankAccountUpdate(BaseModel):
    """은행 계좌 수정 요청 스키마."""

    account_name: str | None = None
    bank_name: str | None = None
    account_number: str | None = None
    currency: str | None = None
    balance: Decimal | None = None
    is_active: bool | None = None


class BankAccount(BaseDocument):
    """은행 계좌 문서."""

    account_name: str = ""
    bank_name: str = ""
    account_number: str = ""
    currency: str = "KRW"
    balance: Decimal = Decimal(0)
    is_active: bool = True
