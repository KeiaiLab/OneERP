"""렌탈 주문(RentalOrder) 문서 모델.

고객의 렌탈 계약을 나타내며, 기간·요금·보증금 정보를 관리한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class RentalOrderStatus(StrEnum):
    """렌탈 주문 상태."""

    DRAFT = "draft"
    CONFIRMED = "confirmed"
    ACTIVE = "active"
    OVERDUE = "overdue"
    RETURNED = "returned"
    CANCELLED = "cancelled"


class BillingCycle(StrEnum):
    """청구 주기."""

    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class RentalOrderCreate(BaseModel):
    """렌탈 주문 생성 요청 스키마."""

    customer_id: str
    customer_name: str = ""
    rental_item_id: str = ""
    item_code: str = ""
    start_date: date | None = None
    end_date: date | None = None
    billing_cycle: BillingCycle = BillingCycle.DAILY
    daily_rate: Decimal = Decimal(0)
    deposit_amount: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)
    status: RentalOrderStatus = RentalOrderStatus.DRAFT
    memo: str = ""


class RentalOrderUpdate(BaseModel):
    """렌탈 주문 수정 요청 스키마."""

    customer_id: str | None = None
    customer_name: str | None = None
    rental_item_id: str | None = None
    item_code: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    billing_cycle: BillingCycle | None = None
    daily_rate: Decimal | None = None
    deposit_amount: Decimal | None = None
    total_amount: Decimal | None = None
    status: RentalOrderStatus | None = None
    memo: str | None = None


class RentalOrder(BaseDocument):
    """렌탈 주문 문서.

    렌탈 기간, 요금, 보증금, 청구 주기를 포함한다.
    """

    customer_id: str = ""
    customer_name: str = ""
    rental_item_id: str = ""
    item_code: str = ""
    start_date: date | None = None
    end_date: date | None = None
    billing_cycle: BillingCycle = BillingCycle.DAILY
    daily_rate: Decimal = Decimal(0)
    deposit_amount: Decimal = Decimal(0)
    total_amount: Decimal = Decimal(0)
    status: RentalOrderStatus = RentalOrderStatus.DRAFT
    memo: str = ""
