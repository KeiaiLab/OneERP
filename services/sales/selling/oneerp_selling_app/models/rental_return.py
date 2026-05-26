"""렌탈 반납(RentalReturn) 문서 모델."""

from __future__ import annotations

from datetime import date  # noqa: TC003 — pydantic 요청 바디 검증 런타임 필요
from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class RentalReturnCreate(BaseModel):
    """렌탈 반납 생성 요청 스키마."""

    rental_order_id: str
    return_date: date | None = None
    condition: str = ""
    damage_charge: Decimal = Decimal(0)
    memo: str = ""


class RentalReturnUpdate(BaseModel):
    """렌탈 반납 수정 요청 스키마."""

    rental_order_id: str | None = None
    return_date: date | None = None
    condition: str | None = None
    damage_charge: Decimal | None = None
    memo: str | None = None


class RentalReturn(BaseDocument):
    """렌탈 반납 문서."""

    rental_order_id: str = ""
    return_date: date | None = None
    condition: str = ""
    damage_charge: Decimal = Decimal(0)
    memo: str = ""
