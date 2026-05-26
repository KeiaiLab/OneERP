"""독촉장(Dunning) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — Pydantic v2 런타임 타입 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class DunningCreate(BaseModel):
    """독촉장 생성 요청 스키마."""

    customer: str
    outstanding_amount: Decimal = Decimal(0)
    dunning_level: int = 1
    dunning_date: date | None = None
    dunning_fee: Decimal = Decimal(0)


class DunningUpdate(BaseModel):
    """독촉장 수정 요청 스키마."""

    customer: str | None = None
    outstanding_amount: Decimal | None = None
    dunning_level: int | None = None
    dunning_date: date | None = None
    dunning_fee: Decimal | None = None


class Dunning(BaseDocument):
    """독촉장 문서 — 미수금 독촉 관리.

    naming prefix: DUN
    """

    customer: str = ""
    outstanding_amount: Decimal = Decimal(0)
    dunning_level: int = 1
    dunning_date: date | None = None
    dunning_fee: Decimal = Decimal(0)
