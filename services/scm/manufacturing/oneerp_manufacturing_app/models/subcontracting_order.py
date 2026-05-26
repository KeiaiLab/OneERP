"""외주 가공 주문(SubcontractingOrder) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from enum import StrEnum
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from datetime import date


class SubcontractingOrderStatus(StrEnum):
    """외주 가공 주문 상태."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    RECEIVED = "received"
    COMPLETED = "completed"


class SubcontractingOrderCreate(BaseModel):
    """외주 가공 주문 생성 요청 스키마."""

    supplier_id: str
    item_code: str
    qty: Decimal = Decimal(0)
    expected_delivery: date | None = None
    total_cost: Decimal = Decimal(0)


class SubcontractingOrderUpdate(BaseModel):
    """외주 가공 주문 수정 요청 스키마."""

    supplier_id: str | None = None
    item_code: str | None = None
    qty: Decimal | None = None
    expected_delivery: date | None = None
    total_cost: Decimal | None = None


class SubcontractingOrder(BaseDocument):
    """외주 가공 주문 문서."""

    status: SubcontractingOrderStatus = Field(
        default=SubcontractingOrderStatus.DRAFT,
        description="외주 가공 주문 상태",
    )
    supplier_id: str = ""
    item_code: str = ""
    qty: Decimal = Decimal(0)
    expected_delivery: date | None = None
    total_cost: Decimal = Decimal(0)
