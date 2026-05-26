"""로열티 포인트(LoyaltyPoint) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class LoyaltyPointCreate(BaseModel):
    """로열티 포인트 생성 요청 스키마."""

    customer_id: str
    points_earned: Decimal = Decimal(0)
    points_redeemed: Decimal = Decimal(0)
    balance: Decimal = Decimal(0)
    expiry_date: date | None = None


class LoyaltyPointUpdate(BaseModel):
    """로열티 포인트 수정 요청 스키마."""

    customer_id: str | None = None
    points_earned: Decimal | None = None
    points_redeemed: Decimal | None = None
    balance: Decimal | None = None
    expiry_date: date | None = None


class LoyaltyPoint(BaseDocument):
    """로열티 포인트 문서."""

    customer_id: str = ""
    points_earned: Decimal = Decimal(0)
    points_redeemed: Decimal = Decimal(0)
    balance: Decimal = Decimal(0)
    expiry_date: date | None = None
