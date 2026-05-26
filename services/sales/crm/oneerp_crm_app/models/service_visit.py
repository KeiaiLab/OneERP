"""서비스 방문(ServiceVisit) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class ServiceVisitCreate(BaseModel):
    """서비스 방문 생성 요청 스키마."""

    service_order_id: str
    visit_date: date | None = None
    technician_id: str = ""
    work_done: str = ""
    duration_hours: Decimal = Decimal(0)
    customer_feedback: str = ""


class ServiceVisitUpdate(BaseModel):
    """서비스 방문 수정 요청 스키마."""

    service_order_id: str | None = None
    visit_date: date | None = None
    technician_id: str | None = None
    work_done: str | None = None
    duration_hours: Decimal | None = None
    customer_feedback: str | None = None


class ServiceVisit(BaseDocument):
    """서비스 방문 문서."""

    service_order_id: str = ""
    visit_date: date | None = None
    technician_id: str = ""
    work_done: str = ""
    duration_hours: Decimal = Decimal(0)
    customer_feedback: str = ""
