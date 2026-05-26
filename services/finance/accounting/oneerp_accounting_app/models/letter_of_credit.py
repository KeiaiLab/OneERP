"""신용장(LetterOfCredit) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class LetterOfCreditStatus(StrEnum):
    """신용장 상태."""

    DRAFT = "draft"
    ISSUED = "issued"
    NEGOTIATED = "negotiated"
    SETTLED = "settled"
    EXPIRED = "expired"


class LetterOfCreditCreate(BaseModel):
    """신용장 생성 요청 스키마."""

    lc_number: str
    issuing_bank: str = ""
    beneficiary: str = ""
    amount: Decimal = Decimal(0)
    currency: str = "KRW"
    expiry_date: date | None = None


class LetterOfCreditUpdate(BaseModel):
    """신용장 수정 요청 스키마."""

    lc_number: str | None = None
    issuing_bank: str | None = None
    beneficiary: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    expiry_date: date | None = None


class LetterOfCredit(BaseDocument):
    """신용장 문서."""

    status: LetterOfCreditStatus = Field(
        default=LetterOfCreditStatus.DRAFT,
        description="신용장 상태",
    )
    lc_number: str = ""
    issuing_bank: str = ""
    beneficiary: str = ""
    amount: Decimal = Decimal(0)
    currency: str = "KRW"
    expiry_date: date | None = None
