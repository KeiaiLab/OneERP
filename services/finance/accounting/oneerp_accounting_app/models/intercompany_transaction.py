"""내부거래(IntercompanyTransaction) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class IntercompanyTransactionStatus(StrEnum):
    """내부거래 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    ELIMINATED = "eliminated"


class IntercompanyTransactionCreate(BaseModel):
    """내부거래 생성 요청 스키마."""

    from_company: str
    to_company: str
    amount: Decimal = Decimal(0)
    currency: str = "KRW"
    description: str = ""
    transaction_date: date | None = None


class IntercompanyTransactionUpdate(BaseModel):
    """내부거래 수정 요청 스키마."""

    from_company: str | None = None
    to_company: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    description: str | None = None
    transaction_date: date | None = None


class IntercompanyTransaction(BaseDocument):
    """내부거래 문서."""

    status: IntercompanyTransactionStatus = Field(
        default=IntercompanyTransactionStatus.DRAFT,
        description="내부거래 상태",
    )
    from_company: str = ""
    to_company: str = ""
    amount: Decimal = Decimal(0)
    currency: str = "KRW"
    description: str = ""
    transaction_date: date | None = None
