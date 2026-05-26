"""서비스 주문(ServiceOrder) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class ServiceOrderCreate(BaseModel):
    """서비스 주문 생성 요청 스키마."""

    customer_id: str
    service_type: str = ""
    description: str = ""
    priority: str = ""
    scheduled_date: date | None = None
    total_cost: Decimal = Decimal(0)


class ServiceOrderUpdate(BaseModel):
    """서비스 주문 수정 요청 스키마."""

    customer_id: str | None = None
    service_type: str | None = None
    description: str | None = None
    priority: str | None = None
    scheduled_date: date | None = None
    total_cost: Decimal | None = None


class ServiceOrder(BaseDocument):
    """서비스 주문 문서."""

    customer_id: str = ""
    service_type: str = ""
    description: str = ""
    priority: str = ""
    scheduled_date: date | None = None
    total_cost: Decimal = Decimal(0)
