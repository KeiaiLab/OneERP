"""로열티 프로그램 및 포인트 모델 — 고객 포인트 적립·사용을 관리한다."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date, datetime


class EarningRule(BaseModel):
    """포인트 적립 규칙."""

    min_amount: Decimal = Decimal(0)
    points: int = 0
    multiplier: Decimal = Decimal(1)


class RedemptionRule(BaseModel):
    """포인트 사용 규칙."""

    points: int = 0
    discount_amount: Decimal = Decimal(0)


class LoyaltyProgramCreate(BaseModel):
    """로열티 프로그램 생성 요청 스키마."""

    program_name: str
    earning_rules: list[EarningRule] = []
    redemption_rules: list[RedemptionRule] = []
    expiry_months: int = 12
    is_active: bool = True
    company: str = ""


class LoyaltyProgramUpdate(BaseModel):
    """로열티 프로그램 수정 요청 스키마."""

    program_name: str | None = None
    earning_rules: list[EarningRule] | None = None
    redemption_rules: list[RedemptionRule] | None = None
    expiry_months: int | None = None
    is_active: bool | None = None


class LoyaltyProgram(BaseDocument):
    """로열티 프로그램 문서 — 포인트 적립·사용 규칙을 저장한다."""

    program_name: str = ""
    earning_rules: list[EarningRule] = []
    redemption_rules: list[RedemptionRule] = []
    expiry_months: int = 12
    is_active: bool = True
    company: str = ""


class LoyaltyPointCreate(BaseModel):
    """포인트 내역 생성 요청 스키마."""

    customer_id: str
    program_id: str
    transaction_type: str  # earn/redeem/expire/adjust
    points: int
    reference_doc: str = ""


class LoyaltyPointUpdate(BaseModel):
    """포인트 내역 수정 요청 스키마."""

    points: int | None = None
    reference_doc: str | None = None


class LoyaltyPoint(BaseDocument):
    """포인트 내역 문서 — 고객 포인트 거래를 저장한다."""

    customer_id: str = ""
    program_id: str = ""
    transaction_type: str = ""  # earn/redeem/expire/adjust
    points: int = 0
    reference_doc: str = ""
    transaction_date: datetime | None = None
    expiry_date: date | None = None
