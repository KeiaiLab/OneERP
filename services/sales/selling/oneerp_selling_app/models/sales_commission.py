"""판매 수수료(SalesCommission) 문서 모델.

L2 비즈니스 룰 매핑:
- BR-SELL-018: 수수료 = 매출액 x commission_rate (미설정 시 0%)
"""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, model_validator


def calculate_commission(sales_amount: Decimal, commission_rate: Decimal) -> Decimal:
    """BR-SELL-018: 영업사원 수수료를 계산한다.

    수수료 = 매출액 x commission_rate / 100
    commission_rate 미설정(0) 시 수수료 0.
    """
    if commission_rate <= 0:
        return Decimal(0)
    return (sales_amount * commission_rate / Decimal(100)).quantize(
        Decimal(1), rounding=ROUND_HALF_UP
    )


class SalesCommissionCreate(BaseModel):
    """판매 수수료 생성 요청 스키마."""

    sales_person_id: str
    sales_order_id: str = ""
    commission_rate: Decimal = Decimal(0)
    commission_amount: Decimal = Decimal(0)
    is_paid: bool = False

    @model_validator(mode="after")
    def _자동_수수료_계산(self) -> SalesCommissionCreate:
        """BR-SELL-018: commission_amount가 0이고 rate가 있으면 자동 계산은 생략 (외부에서 설정)."""
        return self


class SalesCommissionUpdate(BaseModel):
    """판매 수수료 수정 요청 스키마."""

    sales_person_id: str | None = None
    sales_order_id: str | None = None
    commission_rate: Decimal | None = None
    commission_amount: Decimal | None = None
    is_paid: bool | None = None


class SalesCommission(BaseDocument):
    """판매 수수료 문서."""

    sales_person_id: str = ""
    sales_order_id: str = ""
    commission_rate: Decimal = Decimal(0)
    commission_amount: Decimal = Decimal(0)
    is_paid: bool = False
