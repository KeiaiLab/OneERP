"""헤징 수단(HedgingInstrument) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class HedgingInstrumentStatus(StrEnum):
    """헤징 수단 상태."""

    ACTIVE = "active"
    MATURED = "matured"
    TERMINATED = "terminated"


class HedgingInstrumentCreate(BaseModel):
    """헤징 수단 생성 요청 스키마."""

    instrument_type: str
    notional_amount: Decimal = Decimal(0)
    currency: str = ""
    maturity_date: date | None = None
    counterparty: str = ""


class HedgingInstrumentUpdate(BaseModel):
    """헤징 수단 수정 요청 스키마."""

    instrument_type: str | None = None
    notional_amount: Decimal | None = None
    currency: str | None = None
    maturity_date: date | None = None
    counterparty: str | None = None


class HedgingInstrument(BaseDocument):
    """헤징 수단 문서."""

    status: HedgingInstrumentStatus = Field(
        default=HedgingInstrumentStatus.ACTIVE,
        description="헤징 수단 상태",
    )
    instrument_type: str = ""
    notional_amount: Decimal = Decimal(0)
    currency: str = ""
    maturity_date: date | None = None
    counterparty: str = ""
