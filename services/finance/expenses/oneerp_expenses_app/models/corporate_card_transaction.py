"""법인카드거래(CorporateCardTransaction) 문서 모델 — Expenses 모듈."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class CorporateCardTransactionCreate(BaseModel):
    """법인카드거래 생성 요청 스키마."""

    card_number: str
    transaction_date: date | None = None
    merchant: str = ""
    amount: Decimal = Decimal(0)


class CorporateCardTransactionUpdate(BaseModel):
    """법인카드거래 수정 요청 스키마."""

    card_number: str | None = None
    transaction_date: date | None = None
    merchant: str | None = None
    amount: Decimal | None = None


class CorporateCardTransaction(BaseDocument):
    """법인카드거래 문서 — Expenses 법인카드 거래 로그.

    naming prefix: CCT
    """

    card_number: str = ""
    transaction_date: date | None = None
    merchant: str = ""
    amount: Decimal = Decimal(0)
