"""렌탈 품목(RentalItem) 문서 모델.

렌탈 가능한 자산/장비의 마스터 데이터를 정의한다.
일일 요금, 가용 상태, 상태 정보를 관리한다.
"""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field


class RentalItemStatus(StrEnum):
    """렌탈 품목 가용 상태."""

    AVAILABLE = "available"
    RENTED = "rented"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"


class RentalItemCreate(BaseModel):
    """렌탈 품목 생성 요청 스키마."""

    item_code: str
    item_name: str = ""
    category: str = ""
    daily_rate: Decimal = Decimal(0)
    weekly_rate: Decimal = Decimal(0)
    monthly_rate: Decimal = Decimal(0)
    deposit_amount: Decimal = Decimal(0)
    status: RentalItemStatus = RentalItemStatus.AVAILABLE
    condition: str = ""
    serial_no: str = ""
    warehouse: str = ""


class RentalItemUpdate(BaseModel):
    """렌탈 품목 수정 요청 스키마."""

    item_code: str | None = None
    item_name: str | None = None
    category: str | None = None
    daily_rate: Decimal | None = None
    weekly_rate: Decimal | None = None
    monthly_rate: Decimal | None = None
    deposit_amount: Decimal | None = None
    status: RentalItemStatus | None = None
    condition: str | None = None
    serial_no: str | None = None
    warehouse: str | None = None


class RentalItem(BaseDocument):
    """렌탈 품목 문서.

    렌탈 가능 자산의 기본 정보, 요금, 가용 상태를 저장한다.
    """

    item_code: str = ""
    item_name: str = ""
    category: str = ""
    daily_rate: Decimal = Decimal(0)
    weekly_rate: Decimal = Decimal(0)
    monthly_rate: Decimal = Decimal(0)
    deposit_amount: Decimal = Decimal(0)
    status: RentalItemStatus = RentalItemStatus.AVAILABLE
    condition: str = ""
    serial_no: str = ""
    warehouse: str = ""
    total_rental_count: int = Field(default=0, description="누적 렌탈 횟수")
