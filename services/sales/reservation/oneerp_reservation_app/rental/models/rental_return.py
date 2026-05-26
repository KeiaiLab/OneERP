"""렌탈 반납(RentalReturn) 문서 모델.

렌탈 품목의 반납 정보와 손상 비용을 관리한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class ReturnCondition(StrEnum):
    """반납 상태."""

    GOOD = "good"
    FAIR = "fair"
    DAMAGED = "damaged"
    LOST = "lost"


class RentalReturnCreate(BaseModel):
    """렌탈 반납 생성 요청 스키마."""

    rental_order_id: str
    return_date: date | None = None
    condition: ReturnCondition = ReturnCondition.GOOD
    damage_charge: Decimal = Decimal(0)
    late_fee: Decimal = Decimal(0)
    deposit_refund: Decimal = Decimal(0)
    memo: str = ""


class RentalReturnUpdate(BaseModel):
    """렌탈 반납 수정 요청 스키마."""

    rental_order_id: str | None = None
    return_date: date | None = None
    condition: ReturnCondition | None = None
    damage_charge: Decimal | None = None
    late_fee: Decimal | None = None
    deposit_refund: Decimal | None = None
    memo: str | None = None


class RentalReturn(BaseDocument):
    """렌탈 반납 문서.

    반납 일자, 상태, 손상 비용, 연체료, 보증금 환불 정보를 포함한다.
    """

    rental_order_id: str = ""
    return_date: date | None = None
    condition: ReturnCondition = ReturnCondition.GOOD
    damage_charge: Decimal = Decimal(0)
    late_fee: Decimal = Decimal(0)
    deposit_refund: Decimal = Decimal(0)
    memo: str = ""
