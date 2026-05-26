"""유지보수 방문(MaintenanceVisit) 문서 모델."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from oneerp_core.document import BaseDocument
from pydantic import BaseModel

if TYPE_CHECKING:
    from datetime import date


class MaintenanceVisitCreate(BaseModel):
    """유지보수 방문 생성 요청 스키마."""

    maintenance_request_id: str
    visit_date: date | None = None
    technician: str = ""
    work_done: str = ""
    duration_hours: Decimal = Decimal(0)
    cost: Decimal = Decimal(0)


class MaintenanceVisitUpdate(BaseModel):
    """유지보수 방문 수정 요청 스키마."""

    maintenance_request_id: str | None = None
    visit_date: date | None = None
    technician: str | None = None
    work_done: str | None = None
    duration_hours: Decimal | None = None
    cost: Decimal | None = None


class MaintenanceVisit(BaseDocument):
    """유지보수 방문 문서."""

    maintenance_request_id: str = ""
    visit_date: date | None = None
    technician: str = ""
    work_done: str = ""
    duration_hours: Decimal = Decimal(0)
    cost: Decimal = Decimal(0)
