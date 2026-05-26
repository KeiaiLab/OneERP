"""렌탈 주문(RentalOrder) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class RentalOrderCreate(BaseModel):
    """렌탈 주문 생성 요청 스키마."""

    customer_id: str
    rental_item_id: str = ""
    start_date: date | None = None
    end_date: date | None = None
    daily_rate: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)


class RentalOrderUpdate(BaseModel):
    """렌탈 주문 수정 요청 스키마."""

    customer_id: str | None = None
    rental_item_id: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    daily_rate: Decimal | None = None
    total_amount: Decimal | None = None


class RentalOrder(BaseDocument):
    """렌탈 주문 문서."""

    customer_id: str = ""
    rental_item_id: str = ""
    start_date: date | None = None
    end_date: date | None = None
    daily_rate: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)
