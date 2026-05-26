"""로열티 프로그램(LoyaltyProgram) 문서 모델."""

from __future__ import annotations

from decimal import Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel


class LoyaltyProgramCreate(BaseModel):
    """로열티 프로그램 생성 요청 스키마."""

    program_name: str
    points_per_amount: Decimal = Decimal(0)
    min_purchase: Decimal = Decimal(0)
    expiry_months: int = 12
    is_active: bool = True


class LoyaltyProgramUpdate(BaseModel):
    """로열티 프로그램 수정 요청 스키마."""

    program_name: str | None = None
    points_per_amount: Decimal | None = None
    min_purchase: Decimal | None = None
    expiry_months: int | None = None
    is_active: bool | None = None


class LoyaltyProgram(BaseDocument):
    """로열티 프로그램 문서."""

    program_name: str = ""
    points_per_amount: Decimal = Decimal(0)
    min_purchase: Decimal = Decimal(0)
    expiry_months: int = 12
    is_active: bool = True
