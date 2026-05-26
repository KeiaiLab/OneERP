"""환율(Currency Exchange) 문서 모델 — 마스터 데이터."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class CurrencyExchangeCreate(BaseModel):
    """환율 생성 요청 스키마."""

    from_currency: str = ""
    to_currency: str = ""
    exchange_rate: Decimal = Decimal(1)
    exchange_date: date | None = None
    for_buying: bool = False
    for_selling: bool = False


class CurrencyExchangeUpdate(BaseModel):
    """환율 수정 요청 스키마."""

    from_currency: str | None = None
    to_currency: str | None = None
    exchange_rate: Decimal | None = None
    exchange_date: date | None = None
    for_buying: bool | None = None
    for_selling: bool | None = None


class CurrencyExchange(BaseDocument):
    """환율 문서 — 통화 간 환율 관리.

    naming prefix: CXR
    """

    from_currency: str = ""
    to_currency: str = ""
    exchange_rate: Decimal = Decimal(1)
    exchange_date: date | None = None
    for_buying: bool = False
    for_selling: bool = False
